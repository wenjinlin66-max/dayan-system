# API 契约模板

## 1. 通用约定
- Base URL：
- 认证方式：
- Content-Type：application/json
- 统一响应结构：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

## 2. 接口清单

### 2.1 创建资源
- Method：POST
- Path：/api/v1/<resource>
- Auth：是/否
- Request Body：

```json
{
  "field": "value"
}
```

- Response 200：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1
  }
}
```

### 2.2 查询资源
- Method：GET
- Path：/api/v1/<resource>/{id}

## 3. 字段契约
- 字段名：
- 类型：
- 必填：是/否
- 默认值：
- 枚举范围：
- 说明：

## 4. 错误码
- 400 参数错误
- 401 未授权
- 403 无权限
- 404 资源不存在
- 409 业务冲突
- 500 服务器异常
