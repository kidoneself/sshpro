#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞牛分享链接解析脚本
用于解析飞牛分享链接，获取文件列表和下载链接
"""

import requests
import re
import json
import time
import hashlib
import random
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Optional

# 尝试导入selenium（可选）
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class FeiNiuShareParser:
    """飞牛分享链接解析器"""
    
    def __init__(self, share_url: str, auth: Optional[str] = None, download_token: Optional[str] = None):
        """
        初始化解析器
        
        Args:
            share_url: 分享链接，例如: https://fn.frp.naspt.vip/s/e403bd7176654230a2
            auth: 可选的auth值，如果提供则直接使用，否则尝试从页面获取
            download_token: 可选的下载token，如果提供则直接使用，否则尝试通过API获取
        """
        self.share_url = share_url
        self.base_url = None
        self.share_id = None
        self.auth = auth
        self.share_file_name = None
        self.share_file_type = 0
        self.download_token = download_token  # 用于下载的token
        self.cookies = {}
        self.session = requests.Session()
        # 明确禁用代理，避免读取环境变量中的代理设置
        self.session.proxies = {}
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Origin': 'https://fn.frp.naspt.vip',
            'Referer': share_url,
        })
        self._parse_share_url()
        if self.auth:
            self.cookies = {self.share_id: self.auth}
    
    def _parse_share_url(self):
        """解析分享URL，提取基础URL和分享ID"""
        parsed = urlparse(self.share_url)
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"
        # 提取分享ID，格式: /s/{shareId}
        match = re.search(r'/s/([a-f0-9]+)', self.share_url)
        if match:
            self.share_id = match.group(1)
        else:
            raise ValueError(f"无法从URL中提取分享ID: {self.share_url}")
    
    def _hash_signature_data(self, data: str) -> str:
        """
        计算请求数据的hash（对应hashSignatureData函数）
        """
        try:
            # 替换 %(不是两位十六进制) 为 %25，然后URL解码
            import re
            from urllib.parse import unquote
            i = re.sub(r'%(?![0-9A-Fa-f]{2})', '%25', data)
            o = unquote(i)
            return hashlib.md5(o.encode()).hexdigest()
        except:
            return hashlib.md5(data.encode()).hexdigest()
    
    def _generate_authx(self, url: str, data: dict = None, api_key: str = "", sign_method: int = 0) -> str:
        """
        生成authx头部（使用从JS代码中提取的真实算法）
        格式: nonce={nonce}&timestamp={timestamp}&sign={sign}
        
        Args:
            url: 请求URL
            data: 请求数据（字典）
            api_key: API密钥（可选）
            sign_method: 签名方法
                0: 使用真实算法（从JS代码提取）
                1-5: 旧的回退方法
        
        算法（从JS代码提取）:
        tt = ["NDzZTVxnRKP8Z0jXg1VAMonaG8akvh", url_path, nonce, timestamp, data_hash, api_key].join("_")
        sign = md5(tt)
        """
        nonce = str(random.randint(100000, 999999))
        timestamp = str(int(time.time() * 1000))  # 必须是字符串，对应JS中的 Date.now()+""
        
        # 方法0: 使用真实算法
        if sign_method == 0:
            secret_key = "NDzZTVxnRKP8Z0jXg1VAMonaG8akvh"
            
            # 解析URL获取路径
            from urllib.parse import urlparse
            parsed = urlparse(url)
            url_path = parsed.path
            
            # 计算请求数据的hash
            if data:
                import json
                data_str = json.dumps(data, separators=(',', ':'))
            else:
                data_str = ""
            
            data_hash = self._hash_signature_data(data_str)
            
            # 如果apiKey为空，使用硬编码的apiKey（从JS代码中提取）
            if not api_key:
                api_key = "814&d6470861a4cfbbb4fe2fd3f$6581f6"
            
            # 构建tt字符串
            tt = f"{secret_key}_{url_path}_{nonce}_{timestamp}_{data_hash}_{api_key}"
            
            # 计算sign
            sign = hashlib.md5(tt.encode()).hexdigest()
        else:
            # 回退到旧方法
            if sign_method == 1 and self.auth:
                sign_str = f"{nonce}{timestamp}{self.auth}"
            elif sign_method == 2:
                sign_str = f"{nonce}{timestamp}{self.share_id}"
            elif sign_method == 3 and self.auth:
                sign_str = f"{self.auth}{nonce}{timestamp}"
            elif sign_method == 4:
                sign_str = f"{self.share_id}{nonce}{timestamp}"
            elif sign_method == 5 and self.auth:
                sign_str = f"{nonce}{self.auth}{timestamp}"
            else:
                sign_str = f"{nonce}{timestamp}{self.share_id}"
            
            sign = hashlib.md5(sign_str.encode()).hexdigest()
        
        return f"nonce={nonce}&timestamp={timestamp}&sign={sign}"
    
    def get_share_info_with_selenium(self) -> Optional[str]:
        """
        使用Selenium自动获取auth值（需要安装selenium和chromedriver）
        
        Returns:
            auth值，如果失败返回None
        """
        if not SELENIUM_AVAILABLE:
            return None
        
        try:
            print("  - 尝试使用Selenium自动获取auth值...")
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(self.share_url)
            
            # 等待页面加载
            time.sleep(3)
            
            # 获取cookies
            cookies = driver.get_cookies()
            driver.quit()
            
            # 查找auth cookie
            for cookie in cookies:
                if cookie['name'] == self.share_id:
                    auth = cookie['value']
                    print(f"  - 从Selenium获取到Auth: {auth}")
                    return auth
            
            return None
        except Exception as e:
            print(f"  - Selenium获取失败: {str(e)}")
            return None
    
    def get_file_list_with_selenium(self) -> List[Dict]:
        """
        使用Selenium直接执行JavaScript获取文件列表
        
        Returns:
            文件列表
        """
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium未安装，无法使用此方法")
        
        try:
            print("  - 使用Selenium执行JavaScript获取文件列表...")
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(self.share_url)
            
            # 等待页面加载
            time.sleep(5)
            
            # 执行JavaScript获取文件列表
            # 尝试从页面中获取文件列表数据
            try:
                # 等待页面加载完成
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                
                # 尝试获取文件列表（通过执行页面中的函数或访问全局变量）
                file_list_script = """
                // 尝试从页面中获取文件列表
                if (window.__fileList) {
                    return window.__fileList;
                }
                // 尝试触发文件列表加载
                if (window.loadFileList) {
                    window.loadFileList();
                    return new Promise((resolve) => {
                        setTimeout(() => {
                            resolve(window.__fileList || []);
                        }, 2000);
                    });
                }
                return [];
                """
                
                file_list = driver.execute_async_script(file_list_script)
                
                if file_list:
                    print(f"  - 成功获取到 {len(file_list)} 个文件")
                    driver.quit()
                    return file_list
            except Exception as e:
                print(f"  - JavaScript执行失败: {str(e)}")
            
            # 如果JavaScript方法失败，尝试从网络请求中拦截
            # 获取浏览器的网络日志
            logs = driver.get_log('performance')
            for log in logs:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    url = message['message']['params']['response']['url']
                    if '/api/v1/share/list' in url:
                        # 找到了列表请求
                        request_id = message['message']['params']['requestId']
                        # 尝试获取响应内容
                        response = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                        if response and 'body' in response:
                            try:
                                result = json.loads(response['body'])
                                if isinstance(result, dict) and 'data' in result:
                                    file_list = result['data'].get('files', [])
                                    if file_list:
                                        print(f"  - 从网络请求中获取到 {len(file_list)} 个文件")
                                        driver.quit()
                                        return file_list
                            except:
                                pass
            
            driver.quit()
            return []
            
        except Exception as e:
            raise Exception(f"Selenium获取文件列表失败: {str(e)}")
    
    def get_file_list_via_api_intercept(self) -> List[Dict]:
        """
        通过拦截API请求获取文件列表（使用Selenium + CDP）
        """
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium未安装，无法使用此方法")
        
        try:
            print("  - 使用Selenium拦截API请求...")
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            
            driver = webdriver.Chrome(options=chrome_options)
            
            # 启用网络日志
            driver.execute_cdp_cmd('Network.enable', {})
            driver.execute_cdp_cmd('Runtime.enable', {})
            
            driver.get(self.share_url)
            
            # 等待页面加载和API请求
            time.sleep(8)
            
            # 获取所有网络日志
            logs = driver.get_log('performance')
            file_list = []
            
            for log in logs:
                try:
                    message = json.loads(log['message'])
                    method = message['message']['method']
                    params = message['message'].get('params', {})
                    
                    # 查找响应接收事件
                    if method == 'Network.responseReceived':
                        response = params.get('response', {})
                        url = response.get('url', '')
                        
                        if '/api/v1/share/list' in url:
                            request_id = params.get('requestId')
                            # 获取响应体
                            try:
                                response_body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                                if response_body and 'body' in response_body:
                                    result = json.loads(response_body['body'])
                                    if isinstance(result, dict):
                                        if result.get('code') == 0 and 'data' in result:
                                            file_list = result['data'].get('files', [])
                                            if file_list:
                                                print(f"  - 成功拦截到 {len(file_list)} 个文件")
                                                break
                            except Exception as e:
                                print(f"  - 获取响应体失败: {str(e)}")
                                continue
                
                except Exception as e:
                    continue
            
            driver.quit()
            return file_list
            
        except Exception as e:
            raise Exception(f"API拦截失败: {str(e)}")
    
    def get_share_info(self) -> Dict:
        """
        访问分享页面，获取认证信息
        
        Returns:
            包含认证信息的字典
        """
        try:
            response = self.session.get(self.share_url, timeout=10)
            response.raise_for_status()
            
            # 从cookie中获取auth值
            cookies = self.session.cookies.get_dict()
            print(f"  - 获取到的Cookies: {cookies}")
            
            if self.share_id in cookies:
                self.auth = cookies[self.share_id]
                self.cookies = {self.share_id: self.auth}
                print(f"  - 从Cookie中获取到Auth: {self.auth}")
            
            # 尝试从页面HTML中提取auth值（如果cookie中没有）
            if not self.auth:
                html = response.text
                
                # 优先从 share-data script 标签中提取token
                share_data_match = re.search(r'<script[^>]*id=["\']share-data["\'][^>]*>(.*?)</script>', html, re.DOTALL | re.I)
                if share_data_match:
                    try:
                        share_data_json = json.loads(share_data_match.group(1))
                        if isinstance(share_data_json, dict):
                            data = share_data_json.get('data', {})
                            token = data.get('token')
                            if token:
                                self.auth = token
                                # 保存页面token，可能用作apiKey
                                self.page_token = token
                                # 只有在没有提供download_token时才使用页面token
                                if not self.download_token:
                                    self.download_token = token  # 这个token可能就是下载token（但可能不正确）
                                self.cookies = {self.share_id: self.auth}
                                # 保存文件信息（如果有）
                                self.share_file_name = data.get('name', '')
                                self.share_file_type = data.get('type', 0)
                                print(f"  - 从share-data中提取到Token: {self.auth}")
                                if self.share_file_name:
                                    print(f"  - 文件名: {self.share_file_name}")
                                    print(f"  - 可以直接使用token构建下载链接")
                    except json.JSONDecodeError:
                        pass
                
                # 如果还没有，尝试其他模式匹配auth值
                if not self.auth:
                    patterns = [
                        r'auth["\']?\s*[:=]\s*["\']([a-f0-9]{16,})["\']',
                        r'"auth"\s*:\s*"([a-f0-9]{16,})"',
                        r"'auth'\s*:\s*'([a-f0-9]{16,})'",
                        r'auth\s*=\s*["\']([a-f0-9]{16,})["\']',
                        r'"token"\s*:\s*"([a-f0-9]{16,})"',  # 也尝试匹配token
                    ]
                    
                    for pattern in patterns:
                        auth_match = re.search(pattern, html, re.I)
                        if auth_match:
                            self.auth = auth_match.group(1)
                            self.cookies = {self.share_id: self.auth}
                            print(f"  - 从HTML中提取到Auth: {self.auth}")
                            break
            
            # 如果还是没有，尝试从响应头或set-cookie中获取
            if not self.auth:
                set_cookie = response.headers.get('Set-Cookie', '')
                print(f"  - Set-Cookie头: {set_cookie}")
                if set_cookie:
                    match = re.search(rf'{self.share_id}=([^;]+)', set_cookie)
                    if match:
                        self.auth = match.group(1)
                        self.cookies = {self.share_id: self.auth}
                        print(f"  - 从Set-Cookie中获取到Auth: {self.auth}")
            
            # 如果还是没有，尝试使用Selenium
            if not self.auth:
                self.auth = self.get_share_info_with_selenium()
                if self.auth:
                    self.cookies = {self.share_id: self.auth}
            
            # 如果仍然没有auth，尝试使用share_id作为默认值（某些情况下可能有效）
            if not self.auth:
                print("  - 警告: 无法从页面获取auth值，尝试使用share_id")
                self.auth = self.share_id
                self.cookies = {self.share_id: self.share_id}
            
            return {
                'auth': self.auth,
                'cookies': self.cookies,
                'share_id': self.share_id
            }
            
        except Exception as e:
            raise Exception(f"获取分享信息失败: {str(e)}")
    
    def get_file_list_with_real_auth(self, auth: str, authx: str, cookies: dict) -> List[Dict]:
        """
        使用真实的auth和authx获取文件列表（不需要签名算法）
        
        Args:
            auth: 真实的auth值
            authx: 真实的authx值（包含nonce、timestamp、sign）
            cookies: cookie字典
            
        Returns:
            文件列表
        """
        url = f"{self.base_url}/s/{self.share_id}/api/v1/share/list"
        
        headers = {
            'Content-Type': 'application/json',
            'Auth': auth,
            'AuthX': authx,
        }
        
        data = {
            "shareId": self.share_id,
            "path": "/",
            "fileId": None
        }
        
        try:
            response = self.session.post(
                url,
                headers=headers,
                cookies=cookies,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            # 检查是否是错误响应
            if isinstance(result, dict) and result.get('code') == 5000:
                raise Exception(f"API错误: {result.get('msg', 'unknown error')}")
            
            # 返回文件列表
            if isinstance(result, dict):
                if 'data' in result and result['data']:
                    return result['data'].get('files', [])
                elif 'files' in result:
                    return result['files']
                elif 'list' in result:
                    return result['list']
            elif isinstance(result, list):
                return result
            
            return []
                
        except Exception as e:
            raise Exception(f"获取文件列表失败: {str(e)}")
    
    def get_file_list(self, path: str = "/", sign_method: int = 0) -> List[Dict]:
        """
        获取文件列表
        
        Args:
            path: 要列出的路径，默认为根路径
            
        Returns:
            文件列表
        """
        if not self.auth:
            self.get_share_info()
        
        url = f"{self.base_url}/s/{self.share_id}/api/v1/share/list"
        
        data = {
            "shareId": self.share_id,
            "path": path,
            "fileId": None
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Auth': self.auth,
            'AuthX': self._generate_authx(url, data, api_key="", sign_method=sign_method),
        }
        
        try:
            # 重要：必须使用data参数发送已序列化的字符串，而不是json参数
            # 因为签名计算使用的是序列化后的字符串，必须保持一致
            import json
            data_str = json.dumps(data, separators=(',', ':'))
            response = self.session.post(
                url,
                headers=headers,
                cookies=self.cookies,
                data=data_str,  # 使用data而不是json，确保格式一致
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            # 检查是否是错误响应
            if isinstance(result, dict) and result.get('code') == 5000:
                raise Exception(f"API错误: {result.get('msg', 'unknown error')}")
            
            # 返回文件列表
            if isinstance(result, dict):
                if 'data' in result and result['data']:
                    return result['data'].get('files', [])
                elif 'files' in result:
                    return result['files']
                elif 'list' in result:
                    return result['list']
            elif isinstance(result, list):
                return result
            
            return []
                
        except Exception as e:
            print(f"  - 错误详情: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_content = e.response.text
                    print(f"  - 错误响应内容: {error_content}")
                except:
                    pass
            raise Exception(f"获取文件列表失败: {str(e)}")
    
    def get_download_link_with_real_auth(self, files: List[Dict], auth: str, authx: str, cookies: dict, download_filename: str = "飞牛分享文件") -> Optional[str]:
        """
        使用真实的auth和authx获取下载链接
        
        Args:
            files: 文件列表
            auth: 真实的auth值
            authx: 真实的authx值
            cookies: cookie字典
            download_filename: 下载文件名
            
        Returns:
            下载链接
        """
        if not files:
            raise ValueError("文件列表不能为空")
        
        url = f"{self.base_url}/s/{self.share_id}/api/v1/share/download"
        
        headers = {
            'Content-Type': 'application/json',
            'Auth': auth,
            'AuthX': authx,
        }
        
        data = {
            "files": files,
            "shareId": self.share_id,
            "downloadFilename": download_filename
        }
        
        try:
            response = self.session.post(
                url,
                headers=headers,
                cookies=cookies,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            # 从响应中提取下载链接
            if isinstance(result, dict):
                # 打印完整响应以便调试
                print(f"  - 下载API响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # 可能的字段名: downloadUrl, url, link, token
                download_url = (
                    result.get('data', {}).get('downloadUrl') or
                    result.get('data', {}).get('url') or
                    result.get('data', {}).get('link') or
                    result.get('downloadUrl') or
                    result.get('url') or
                    result.get('link')
                )
                
                # 如果有token，构建下载链接（优先使用data中的token）
                token = (
                    result.get('data', {}).get('token') or
                    result.get('token') or
                    result.get('data', {}).get('downloadToken')
                )
                
                if token:
                    download_url = f"{self.base_url}/s/download/{self.share_id}?token={token}"
                    self.download_token = token  # 保存下载token
                
                return download_url
            else:
                return None
                
        except Exception as e:
            raise Exception(f"获取下载链接失败: {str(e)}")
    
    def get_download_link(self, files: List[Dict], download_filename: str = "飞牛分享文件", sign_method: int = 0) -> Optional[str]:
        """
        获取下载链接
        
        Args:
            files: 文件列表，每个文件包含 path 和 fileId
            download_filename: 下载文件名
            
        Returns:
            下载链接，如果失败返回None
        """
        if not self.auth:
            self.get_share_info()
        
        if not files:
            raise ValueError("文件列表不能为空")
        
        url = f"{self.base_url}/s/{self.share_id}/api/v1/share/download"
        
        # 构建files数组，确保path包含完整路径
        files_data = []
        for f in files:
            file_path = f.get('path', '')
            file_name = f.get('file', '')
            # 如果path为空，使用文件名构建完整路径（以/开头）
            if not file_path and file_name:
                file_path = f"/{file_name}"
            files_data.append({
                "path": file_path,
                "fileId": f.get('fileId')
            })
        
        data = {
            "files": files_data,
            "shareId": self.share_id,
            "downloadFilename": download_filename
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Auth': self.auth,
            'AuthX': self._generate_authx(url, data, api_key="", sign_method=sign_method),
        }
        
        try:
            # 重要：必须使用data参数发送已序列化的字符串，而不是json参数
            # 因为签名计算使用的是序列化后的字符串，必须保持一致
            import json
            data_str = json.dumps(data, separators=(',', ':'))
            response = self.session.post(
                url,
                headers=headers,
                cookies=self.cookies,
                data=data_str,  # 使用data而不是json，确保格式一致
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            # 从响应中提取下载链接
            if isinstance(result, dict):
                # 打印完整响应以便调试
                print(f"  - 下载API响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                data_obj = result.get('data', {})
                
                # 优先检查path字段（API返回的格式：/s/download/{shareId}?token=xxx）
                path = data_obj.get('path')
                if path:
                    # 如果path是完整URL，直接使用
                    if path.startswith('http'):
                        download_url = path
                    # 如果path是相对路径，拼接base_url
                    elif path.startswith('/'):
                        download_url = f"{self.base_url}{path}"
                    else:
                        download_url = f"{self.base_url}/{path}"
                    
                    # 从path中提取token
                    token_match = re.search(r'token=([a-f0-9]+)', path)
                    if token_match:
                        self.download_token = token_match.group(1)
                    
                    return download_url
                
                # 如果没有path，尝试其他字段
                download_url = (
                    data_obj.get('downloadUrl') or
                    data_obj.get('url') or
                    data_obj.get('link') or
                    result.get('downloadUrl') or
                    result.get('url') or
                    result.get('link')
                )
                
                # 如果有token，构建下载链接（优先使用data中的token）
                token = (
                    data_obj.get('token') or
                    result.get('token') or
                    data_obj.get('downloadToken')
                )
                
                if token:
                    download_url = f"{self.base_url}/s/download/{self.share_id}?token={token}"
                    self.download_token = token  # 保存下载token
                
                return download_url
            else:
                return None
                
        except Exception as e:
            raise Exception(f"获取下载链接失败: {str(e)}")
    
    def download_file(self, download_url: str, save_path: str = None, chunk_size: int = 8192) -> str:
        """
        下载文件
        
        Args:
            download_url: 下载链接
            save_path: 保存路径，如果为None则使用文件名
            chunk_size: 下载块大小
            
        Returns:
            保存的文件路径
        """
        import os
        from urllib.parse import urlparse, parse_qs
        
        # 确保有auth和cookie
        if not self.auth:
            self.get_share_info()
        
        # 从URL中提取文件名（如果有）
        parsed = urlparse(download_url)
        query_params = parse_qs(parsed.query)
        
        # 如果没有指定保存路径，尝试从URL或响应头获取文件名
        if not save_path:
            # 尝试从Content-Disposition头获取文件名
            response = self.session.head(download_url, cookies=self.cookies, allow_redirects=True)
            content_disposition = response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"\'')
                save_path = filename
            else:
                # 默认使用share_id作为文件名
                save_path = f"download_{self.share_id}.bin"
        
        # 确保目录存在
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        
        # 下载文件
        headers = {
            'Referer': f'{self.base_url}/s/{self.share_id}',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        }
        
        print(f"  开始下载到: {save_path}")
        response = self.session.get(download_url, headers=headers, cookies=self.cookies, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('Content-Length', 0))
        downloaded = 0
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r  进度: {percent:.1f}% ({downloaded}/{total_size} 字节)", end='', flush=True)
        
        print(f"\n  ✓ 下载完成: {save_path}")
        return save_path
    
    def parse_all(self) -> Dict:
        """
        解析分享链接，获取所有信息
        
        Returns:
            包含文件列表和下载链接的字典
        """
        print(f"正在解析分享链接: {self.share_url}")
        
        # 1. 获取分享信息
        print("步骤1: 获取分享信息...")
        share_info = self.get_share_info()
        print(f"  - 分享ID: {self.share_id}")
        print(f"  - Auth: {self.auth}")
        
        # 2. 获取文件列表
        print("\n步骤2: 获取文件列表...")
        file_list = []
        successful_method = None
        
        # 首先尝试使用Selenium拦截API请求（最可靠的方法）
        if SELENIUM_AVAILABLE:
            try:
                print("  - 尝试使用Selenium拦截API请求...")
                file_list = self.get_file_list_via_api_intercept()
                if file_list:
                    successful_method = 'selenium'
                    print(f"  ✓ 成功！使用Selenium拦截方法")
            except Exception as e:
                print(f"  - Selenium拦截失败: {str(e)}")
                print("  - 回退到API请求方法...")
        
        # 如果Selenium失败，尝试API请求方法（尝试不同的签名方法）
        if not file_list:
            for method in range(6):
                try:
                    file_list = self.get_file_list(sign_method=method)
                    # 检查是否成功（有文件列表且不是错误响应）
                    if file_list or (isinstance(file_list, list) and len(file_list) >= 0):
                        # 验证响应不是错误
                        # 如果get_file_list没有抛出异常，说明可能成功了
                        successful_method = method
                        print(f"  ✓ 成功！使用签名方法 {method}")
                        break
                except Exception as e:
                    error_msg = str(e).lower()
                    if "invalid sign" in error_msg or "5000" in error_msg:
                        # 签名错误，继续尝试下一个方法
                        continue
                    else:
                        # 其他错误，直接抛出
                        raise
        
        if successful_method is None:
            print("  - 警告: 所有方法都失败了")
            if not SELENIUM_AVAILABLE:
                print("  - 提示: 可以安装Selenium来自动获取: pip install selenium")
            print("  - 或者从浏览器开发者工具的Network标签中获取 'Auth' 值")
            print("  - 然后使用: python parse_share_link.py <链接> <auth值>")
        
        print(f"  - 找到 {len(file_list)} 个文件/文件夹")
        for item in file_list:
            item_type = "文件夹" if item.get('isDir') else "文件"
            print(f"    - {item_type}: {item.get('path', 'N/A')} (ID: {item.get('fileId', 'N/A')})")
        
        # 3. 获取下载链接
        download_links = []
        file_download_map = {}  # 文件名 -> 下载链接的映射
        print("\n步骤3: 获取下载链接...")
        
        # 方法1: 如果初始化时提供了下载token（32位），直接使用（优先级最高）
        if download_token := (getattr(self, 'download_token', None) if hasattr(self, 'download_token') else None):
            if download_token and len(download_token) == 32:  # 32位token通常是正确的下载token
                direct_download_link = f"{self.base_url}/s/download/{self.share_id}?token={download_token}"
                download_links.append(direct_download_link)
                print(f"  - 使用提供的下载token构建链接: {direct_download_link}")
        
        # 方法2: 如果有文件列表且签名方法成功，为每个文件单独获取下载链接
        if file_list and successful_method is not None and successful_method != 'selenium':
            # 只下载文件，不下载文件夹
            files_to_download = [f for f in file_list if not f.get('isDir', False)]
            
            if files_to_download:
                print(f"  - 为 {len(files_to_download)} 个文件获取单独的下载链接...")
                for file_item in files_to_download:
                    try:
                        file_name = file_item.get('file', '未知文件')
                        download_link = self.get_download_link([file_item], download_filename=file_name, sign_method=successful_method)
                        if download_link and download_link not in download_links:
                            download_links.append(download_link)
                            file_download_map[file_name] = download_link
                            print(f"    ✓ {file_name}: {download_link}")
                    except Exception as e:
                        print(f"    ✗ {file_name}: 获取失败 - {str(e)}")
        
        if not download_links:
            print("  - 警告: 未能获取下载链接")
        
        return {
            'share_id': self.share_id,
            'share_url': self.share_url,
            'auth': self.auth,
            'files': file_list,
            'download_links': download_links,
            'file_download_map': file_download_map  # 文件名到下载链接的映射
        }


def download_file_from_result(download_url: str, share_id: str, auth: str, share_url: str, save_path: str = None):
    """
    从解析结果下载文件
    
    Args:
        download_url: 下载链接
        share_id: 分享ID
        auth: auth值
        share_url: 分享链接
        save_path: 保存路径
    """
    import re
    
    # 创建session
    session = requests.Session()
    # 明确禁用代理，避免读取环境变量中的代理设置
    session.proxies = {}
    session.cookies.set(share_id, auth)
    
    # 设置请求头（模拟浏览器点击）
    headers = {
        'Referer': share_url,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    
    # 如果没有指定保存路径，从URL或响应头获取
    if not save_path:
        # 先发送HEAD请求获取文件名
        response = session.head(download_url, headers=headers, allow_redirects=True)
        content_disposition = response.headers.get('Content-Disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"\'')
            save_path = filename
        else:
            # 从URL中提取token作为文件名
            token_match = re.search(r'token=([a-f0-9]+)', download_url)
            if token_match:
                save_path = f"file_{token_match.group(1)[:8]}.bin"
            else:
                save_path = f"download_{share_id}.bin"
    
    print(f"下载: {save_path}")
    
    # 下载文件
    response = session.get(download_url, headers=headers, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('Content-Length', 0))
    downloaded = 0
    
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r进度: {percent:.1f}% ({downloaded}/{total_size} 字节)", end='', flush=True)
    
    print(f"\n✓ 下载完成: {save_path} ({downloaded} 字节)")
    return save_path


def main():
    """主函数"""
    import sys
    
    # 检查是否是下载模式（从JSON文件下载）
    if len(sys.argv) >= 2 and sys.argv[1].endswith('.json'):
        # 下载模式
        json_file = sys.argv[1]
        files_to_download = sys.argv[2:] if len(sys.argv) > 2 else None
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            share_id = result['share_id']
            auth = result['auth']
            share_url = result['share_url']
            file_download_map = result.get('file_download_map', {})
            
            print(f"分享ID: {share_id}")
            print(f"Auth: {auth}")
            print(f"找到 {len(file_download_map)} 个文件的下载链接\n")
            
            # 确定要下载的文件
            if files_to_download:
                files = {k: v for k, v in file_download_map.items() if k in files_to_download}
                if not files:
                    print(f"错误: 未找到指定的文件: {', '.join(files_to_download)}")
                    print(f"可用文件: {', '.join(file_download_map.keys())}")
                    sys.exit(1)
            else:
                files = file_download_map
            
            # 下载文件
            for file_name, download_url in files.items():
                try:
                    download_file_from_result(download_url, share_id, auth, share_url, file_name)
                    print()
                except Exception as e:
                    print(f"\n✗ 下载失败: {file_name} - {str(e)}\n")
            
            print(f"完成！已下载 {len(files)} 个文件")
        except Exception as e:
            print(f"错误: {str(e)}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)
        return
    
    # 解析模式
    if len(sys.argv) < 2:
        print("用法:")
        print("  解析分享链接: python parse_share_link.py <分享链接> [auth值] [download_token]")
        print("  下载文件: python parse_share_link.py <share_result.json> [文件1] [文件2] ...")
        print("\n示例:")
        print("  python parse_share_link.py https://fn.frp.naspt.vip/s/53060aaa3fb449dea2")
        print("  python parse_share_link.py share_result_53060aaa3fb449dea2.json")
        print("  python parse_share_link.py share_result_53060aaa3fb449dea2.json clash.tgz roon.tgz")
        print("\n提示:")
        print("  - auth值: 从浏览器开发者工具的Network标签中获取请求头中的 'Auth' 值")
        print("  - download_token: 从浏览器中获取的下载token（32位十六进制字符串）")
        sys.exit(1)
    
    share_url = sys.argv[1]
    auth = sys.argv[2] if len(sys.argv) > 2 else None
    download_token = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        parser = FeiNiuShareParser(share_url, auth=auth, download_token=download_token)
        result = parser.parse_all()
        
        print("\n" + "="*60)
        print("解析结果:")
        print("="*60)
        print(f"分享ID: {result['share_id']}")
        print(f"分享链接: {result['share_url']}")
        print(f"Auth: {result['auth']}")
        print(f"\n文件数量: {len(result['files'])}")
        print(f"下载链接数量: {len(result['download_links'])}")
        
        if result['download_links']:
            print("\n下载链接:")
            # 如果有文件名映射，显示文件名和对应的链接
            if 'file_download_map' in result and result['file_download_map']:
                for file_name, link in result['file_download_map'].items():
                    print(f"  {file_name}: {link}")
            else:
                # 否则只显示链接列表
                for i, link in enumerate(result['download_links'], 1):
                    print(f"  {i}. {link}")
        
        # 保存结果到JSON文件
        output_file = f"share_result_{result['share_id']}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {output_file}")
        print(f"\n下载文件: python parse_share_link.py {output_file} [文件1] [文件2] ...")
        
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

