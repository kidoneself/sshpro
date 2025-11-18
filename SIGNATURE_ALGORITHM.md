# 飞牛分享链接签名算法分析

## 签名算法（从JS代码中提取）

### 算法步骤

1. **secret_key**: `"NDzZTVxnRKP8Z0jXg1VAMonaG8akvh"` (硬编码)

2. **url_path**: URL的路径部分（不含查询参数）
   - 例如: `/s/53060aaa3fb449dea2/api/v1/share/list`

3. **nonce**: 6位随机数（100000-999999）

4. **timestamp**: 当前时间戳（毫秒），转为字符串
   - JS代码: `Date.now()+""`

5. **data_hash**: 请求数据的MD5值
   - 数据: JSON字符串（紧凑格式，无空格）
   - 计算: `MD5(JSON.stringify(data))`

6. **api_key**: `"814&d6470861a4cfbbb4fe2fd3f$6581f6"` (硬编码在JS中)

7. **构建tt字符串**:
   ```
   tt = secret_key + "_" + url_path + "_" + nonce + "_" + timestamp + "_" + data_hash + "_" + api_key
   ```

8. **计算sign**:
   ```
   sign = MD5(tt)
   ```

9. **生成AuthX头部**:
   ```
   AuthX: nonce={nonce}&timestamp={timestamp}&sign={sign}
   ```

### 代码位置

- JS文件: `https://fn.frp.naspt.vip/s/static/0.1.2/main-DcWL7Uny.js`
- 函数: `generateSignature`
- 调用: `withAxiosRequestInterceptor(instance$1, {apiKey:"814&d6470861a4cfbbb4fe2fd3f$6581f6"})`

### 验证

使用真实请求数据验证：
- nonce: `975145`
- timestamp: `1763274866877`
- 期望sign: `0ef1adbff885a57be919b5f79be4c8a3`
- 计算sign: `0ef1adbff885a57be919b5f79be4c8a3` ✅ 匹配

### 实现

已实现到 `parse_share_link.py` 中的 `_generate_authx` 方法。

