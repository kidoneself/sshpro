import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import paramiko
import requests
import time
import base64
import sys
from parse_share_link import FeiNiuShareParser

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")


def ensure_naspt_path(base_path: str) -> str:
    """确保路径以/naspt结尾，并去除多余的斜杠"""
    base = (base_path or '').strip()
    if not base:
        base = '/docker'
    base = base.rstrip('/')
    if not base:
        base = '/docker'
    if not base.endswith('/naspt'):
        base = f"{base}/naspt"
    return base


DEFAULT_REMOTE_BASE_DIR = ensure_naspt_path(os.environ.get('NASPT_REMOTE_BASE_DIR', '/docker'))


def get_remote_paths(docker_path: str | None = None) -> dict:
    """根据Docker配置路径返回统一的naspt目录结构"""
    base_dir = ensure_naspt_path(docker_path) if docker_path else DEFAULT_REMOTE_BASE_DIR
    return {
        'base': base_dir,
        'downloads': f"{base_dir}/downloads",
        'tmp': f"{base_dir}/tmp",
        'compose': f"{base_dir}/compose"
    }


# 存储SSH连接
ssh_connections = {}

# 日志辅助函数，确保立即输出
def log_ssh(msg):
    print(msg)
    sys.stdout.flush()

def create_ssh_connection(host, port, username, password):
    """创建SSH连接"""
    try:
        # 如果用户名不是root，先尝试直接用root用户连接
        if username.lower() != 'root':
            try:
                # 尝试用root用户和相同密码连接
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=host, port=int(port), username='root', password=password, timeout=10)
                username = 'root'  # 标记已切换到root
            except:
                # 如果root连接失败，使用原用户连接
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=host, port=int(port), username=username, password=password, timeout=10)
        else:
            # 如果已经是root，直接连接
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=host, port=int(port), username=username, password=password, timeout=10)
        
        # 如果还不是root，尝试切换到root
        if username.lower() != 'root':
            # 尝试使用exec_command执行sudo切换，验证密码是否正确
            escaped_password = password.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$').replace('`', '\\`').replace('!', '\\!')
            
            # 测试sudo权限和密码
            stdin, stdout, stderr = ssh.exec_command(f'echo "{escaped_password}" | sudo -S whoami', timeout=5)
            result = stdout.read().decode('utf-8').strip()
            
            # 如果sudo成功，说明密码正确，可以在交互式shell中使用
            if result == 'root':
                # 创建交互式shell
                channel = ssh.invoke_shell(term='xterm-256color')
                time.sleep(0.8)
                
                # 在交互式shell中切换到root
                # 先发送sudo -S -i命令
                channel.send('sudo -S -i\n')
                time.sleep(0.8)
                # 发送密码
                channel.send(f'{escaped_password}\n')
                time.sleep(1.5)
                # 确认切换
                channel.send('whoami\n')
                time.sleep(0.3)
            else:
                # sudo失败，使用原用户创建shell
                channel = ssh.invoke_shell(term='xterm-256color')
                time.sleep(0.5)
                channel.send('whoami\n')
        else:
            # 如果已经是root，直接创建shell
            channel = ssh.invoke_shell(term='xterm-256color')
            time.sleep(0.5)
            channel.send('whoami\n')
        
        return ssh, channel
    except Exception as e:
        raise Exception(f"SSH连接失败: {str(e)}")

@socketio.on('connect')
def handle_connect():
    log_ssh('客户端已连接')

@socketio.on('disconnect')
def handle_disconnect():
    log_ssh('客户端已断开')

@socketio.on('ssh_connect')
def handle_ssh_connect(data):
    """处理SSH连接请求"""
    log_ssh(f"[SSH] 收到ssh_connect事件，data={data}")
    try:
        host = data.get('host')
        port = data.get('port', 22)
        username = data.get('username')
        password = data.get('password')
        
        log_ssh(f"[SSH] 解析参数: host={host}, port={port}, username={username}")
        
        if not all([host, username, password]):
            log_ssh("[SSH] 缺少必要参数")
            emit('ssh_error', {'message': '缺少必要参数'})
            return
        
        log_ssh(f"[SSH] 开始创建SSH连接...")
        ssh, channel = create_ssh_connection(host, port, username, password)
        log_ssh(f"[SSH] SSH连接创建成功")
        
        # 存储连接
        session_id = request.sid
        log_ssh(f"[SSH] 建立连接，session_id={session_id}, host={host}, port={port}, username={username}")
        log_ssh(f"[SSH] channel状态: closed={channel.closed}, exit_status_ready={channel.exit_status_ready()}, recv_ready={channel.recv_ready()}")
        
        # 设置channel为非阻塞模式，确保能及时读取数据
        channel.settimeout(0.1)
        
        ssh_connections[session_id] = {
            'ssh': ssh,
            'channel': channel
        }
        
        emit('ssh_connected', {'message': 'SSH连接成功'})
        log_ssh(f"[SSH] 已发送ssh_connected事件")
        
        # 立即读取一次，获取初始输出（比如whoami的结果）
        try:
            if channel.recv_ready():
                initial_data = channel.recv(4096).decode('utf-8', errors='ignore')
                if initial_data:
                    log_ssh(f"[SSH] 初始数据，长度={len(initial_data)}")
                    socketio.emit('ssh_output', {'data': initial_data}, room=session_id)
                    log_ssh(f"[SSH] 已发送初始数据到room={session_id}")
        except Exception as e:
            log_ssh(f"[SSH] 读取初始数据失败: {e}")
        
        # 启动线程读取SSH输出
        def read_ssh_output(target_session_id):
            log_ssh(f"[SSH] 开始读取输出线程，session_id={target_session_id}")
            try:
                while True:
                    try:
                        if target_session_id not in ssh_connections:
                            log_ssh(f"[SSH] session_id不在连接列表中，退出线程")
                            break
                        conn_info = ssh_connections.get(target_session_id)
                        if not conn_info:
                            log_ssh(f"[SSH] 连接信息不存在，退出线程")
                            break
                        channel = conn_info['channel']
                        
                        # 检查channel是否关闭
                        if channel.closed:
                            log_ssh(f"[SSH] channel已关闭，退出线程")
                            break
                        
                        if channel.exit_status_ready():
                            exit_status = channel.recv_exit_status()
                            log_ssh(f"[SSH] channel退出，状态码={exit_status}")
                            break
                        
                        if channel.recv_ready():
                            data = channel.recv(4096).decode('utf-8', errors='ignore')
                            if data:
                                log_ssh(f"[SSH] 收到数据，长度={len(data)}, 内容预览={repr(data[:50])}")
                                try:
                                    socketio.emit('ssh_output', {'data': data}, room=target_session_id)
                                    log_ssh(f"[SSH] 已发送ssh_output事件到room={target_session_id}, 数据长度={len(data)}")
                                except Exception as emit_err:
                                    import traceback
                                    log_ssh(f"[SSH] 发送ssh_output失败: {emit_err}")
                                    log_ssh(f"[SSH] 错误堆栈: {traceback.format_exc()}")
                        else:
                            socketio.sleep(0.05)
                    except Exception as e:
                        import traceback
                        log_ssh(f"[SSH] 读取SSH输出错误: {e}")
                        log_ssh(f"[SSH] 错误堆栈: {traceback.format_exc()}")
                        if target_session_id in ssh_connections:
                            try:
                                socketio.emit('ssh_error', {'message': f'连接已断开: {str(e)}'}, room=target_session_id)
                            except:
                                pass
                        break
            finally:
                log_ssh(f"[SSH] 读取输出线程退出，session_id={target_session_id}")
        
        socketio.start_background_task(read_ssh_output, session_id)
        
    except Exception as e:
        emit('ssh_error', {'message': str(e)})

@socketio.on('ssh_input')
def handle_ssh_input(data):
    """处理SSH输入"""
    try:
        session_id = request.sid
        if session_id in ssh_connections:
            channel = ssh_connections[session_id]['channel']
            command = data.get('command', '')
            if command == '\r':
                command = '\n'
            
            # 记录发送的命令（隐藏敏感字符）
            cmd_display = repr(command) if len(command) == 1 and command in ['\n', '\r', '\t'] else command[:50]
            log_ssh(f"[SSH] 收到输入，session_id={session_id}, command={cmd_display}, channel.closed={channel.closed}")
            
            if channel.closed:
                log_ssh(f"[SSH] channel已关闭，无法发送")
                emit('ssh_error', {'message': 'SSH通道已关闭'})
                return
            
            sent_bytes = channel.send(command)
            log_ssh(f"[SSH] 已发送 {sent_bytes} 字节到channel")
        else:
            log_ssh(f"[SSH] SSH未连接，session_id={session_id}")
            emit('ssh_error', {'message': 'SSH未连接'})
    except Exception as e:
        import traceback
        log_ssh(f"[SSH] 发送输入错误: {e}")
        log_ssh(f"[SSH] 错误堆栈: {traceback.format_exc()}")
        emit('ssh_error', {'message': str(e)})

@socketio.on('ssh_disconnect')
def handle_ssh_disconnect():
    """断开SSH连接"""
    try:
        session_id = request.sid
        if session_id in ssh_connections:
            ssh_connections[session_id]['ssh'].close()
            del ssh_connections[session_id]
            emit('ssh_disconnected', {'message': 'SSH已断开'})
    except Exception as e:
        emit('ssh_error', {'message': str(e)})

@socketio.on('deploy_compose')
def handle_deploy_compose(data):
    """部署Docker Compose配置"""
    try:
        session_id = request.sid
        if session_id not in ssh_connections:
            emit('compose_result', {'success': False, 'message': 'SSH未连接'})
            return
        
        compose_content = data.get('compose', '')
        env_content = data.get('env', '')
        action = data.get('action', 'up')  # up, down, logs
        docker_path = data.get('docker_path')
        
        if not compose_content.strip():
            emit('compose_result', {'success': False, 'message': 'docker-compose.yml内容不能为空'})
            return
        
        ssh = ssh_connections[session_id]['ssh']
        channel = ssh_connections[session_id]['channel']
        
        # 使用持久化目录存放compose文件
        remote_paths = get_remote_paths(docker_path)
        work_dir = remote_paths['compose']
        base_dir = remote_paths['base']
        
        # 创建目录（如果不存在）
        stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {base_dir} {work_dir}', timeout=5)
        stdout.read()  # 等待完成
        
        # 通过SSH命令直接写入文件，避免临时文件问题
        compose_file = f'{work_dir}/docker-compose.yml'
        env_file = f'{work_dir}/.env'
        
        # 上传docker-compose.yml - 使用base64编码避免特殊字符问题
        compose_b64 = base64.b64encode(compose_content.encode('utf-8')).decode('ascii')
        command = f'echo "{compose_b64}" | base64 -d > "{compose_file}"'
        stdin, stdout, stderr = ssh.exec_command(command, timeout=10)
        error = stderr.read().decode('utf-8')
        if error and 'No such file' not in error:  # 忽略目录不存在的错误（会在下面创建）
            raise Exception(f'写入compose文件失败: {error}')
        
        # 上传.env文件（如果有）
        if env_content.strip():
            env_b64 = base64.b64encode(env_content.encode('utf-8')).decode('ascii')
            command = f'echo "{env_b64}" | base64 -d > "{env_file}"'
            stdin, stdout, stderr = ssh.exec_command(command, timeout=10)
            error = stderr.read().decode('utf-8')
            if error:
                raise Exception(f'写入env文件失败: {error}')
        
        # 执行docker-compose命令（支持新格式 docker compose 和旧格式 docker-compose）
        # 先检测使用哪个命令
        test_cmd = 'docker compose version > /dev/null 2>&1 && echo "new" || echo "old"'
        stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=5)
        docker_cmd = stdout.read().decode('utf-8').strip()
        compose_cmd = 'docker compose' if docker_cmd == 'new' else 'docker-compose'
        
        if action == 'up':
            command = f'cd {work_dir} && {compose_cmd} up -d\n'
            emit('compose_result', {'success': True, 'message': '服务启动命令已发送'})
        elif action == 'down':
            command = f'cd {work_dir} && {compose_cmd} down\n'
            emit('compose_result', {'success': True, 'message': '服务停止命令已发送'})
        elif action == 'logs':
            command = f'cd {work_dir} && {compose_cmd} logs --tail=100\n'
            emit('compose_result', {'success': True, 'message': '日志查看命令已发送'})
        else:
            emit('compose_result', {'success': False, 'message': f'未知操作: {action}'})
            return
        
        # 发送命令到终端
        channel.send(command)
        
    except Exception as e:
        emit('compose_result', {'success': False, 'message': str(e)})

@app.route('/api/load-services', methods=['POST'])
def load_services():
    """代理加载服务配置JSON"""
    try:
        data = request.get_json()
        json_url = data.get('url', '').strip()
        
        if not json_url:
            return jsonify({'success': False, 'message': 'URL不能为空'}), 400
        
        # 验证URL格式
        if not json_url.startswith(('http://', 'https://')):
            return jsonify({'success': False, 'message': 'URL格式不正确'}), 400
        
        # 通过服务器获取JSON，避免CORS问题
        # 使用最简单的请求，明确禁用代理
        response = requests.get(
            json_url, 
            timeout=10,
            proxies={}  # 明确禁用代理
        )
        response.raise_for_status()
        
        # 验证返回的是JSON
        try:
            json_data = response.json()
        except ValueError:
            return jsonify({'success': False, 'message': '返回的不是有效的JSON格式'}), 400
        
        # 验证JSON结构
        if not isinstance(json_data, dict) or 'services' not in json_data:
            return jsonify({'success': False, 'message': 'JSON格式错误：缺少services字段'}), 400
        
        return jsonify({'success': True, 'data': json_data})
        
    except requests.exceptions.Timeout as e:
        return jsonify({'success': False, 'message': f'请求超时: {str(e)}。请检查网络连接或目标URL是否可访问'}), 500
    except requests.exceptions.ConnectionError as e:
        error_msg = str(e)
        # 提供更详细的错误信息
        if 'Connection aborted' in error_msg or 'Remote end closed' in error_msg:
            return jsonify({
                'success': False, 
                'message': f'连接被服务器关闭: {error_msg}。可能是目标服务器拒绝连接或网络不稳定，请稍后重试'
            }), 500
        return jsonify({'success': False, 'message': f'连接失败: {error_msg}。请检查网络连接或目标URL是否可访问'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'message': f'请求失败: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

@app.route('/api/parse-share-link', methods=['POST'])
def parse_share_link():
    """解析飞牛分享链接，获取下载地址"""
    try:
        data = request.get_json()
        share_url = data.get('url', '').strip()
        
        if not share_url:
            return jsonify({'success': False, 'message': '分享链接不能为空'}), 400
        
        # 验证URL格式
        if not share_url.startswith(('http://', 'https://')):
            return jsonify({'success': False, 'message': 'URL格式不正确'}), 400
        
        # 使用FeiNiuShareParser解析
        parser = FeiNiuShareParser(share_url)
        result = parser.parse_all()
        
        return jsonify({
            'success': True,
            'data': {
                'share_id': result['share_id'],
                'share_url': result['share_url'],
                'auth': result['auth'],
                'files': result['files'],
                'download_links': result['download_links'],
                'file_download_map': result.get('file_download_map', {})
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'解析失败: {str(e)}'}), 500

@app.route('/')
def index():
    paths = get_remote_paths()
    return render_template(
        'index.html',
        remote_base_dir=paths['base'],
        remote_download_dir=paths['downloads'],
        remote_tmp_dir=paths['tmp']
    )

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=15432, debug=True, allow_unsafe_werkzeug=True)

