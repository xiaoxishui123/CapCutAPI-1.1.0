#!/bin/bash
# 草稿API测试脚本

SERVER_URL="http://8.148.70.18:9000"
echo "=== CapCutAPI 草稿功能测试 ==="
echo "服务器地址: $SERVER_URL"
echo ""

# 1. 测试服务器连接
echo "1. 测试服务器连接..."
if curl -s --connect-timeout 5 "$SERVER_URL/" > /dev/null; then
    echo "✅ 服务器连接正常"
else
    echo "❌ 服务器连接失败"
    exit 1
fi

# 2. 测试草稿列表API
echo -e "\n2. 测试草稿列表API (/api/drafts/list)..."
response=$(curl -s -w "\n%{http_code}" "$SERVER_URL/api/drafts/list")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n -1)

echo "HTTP状态码: $http_code"
if [ "$http_code" = "200" ]; then
    echo "✅ API响应正常"
    echo "响应内容:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo "❌ API响应异常"
    echo "错误内容: $body"
fi

# 3. 测试草稿看板页面
echo -e "\n3. 测试草稿看板页面 (/api/drafts/dashboard)..."
response=$(curl -s -w "\n%{http_code}" "$SERVER_URL/api/drafts/dashboard")
http_code=$(echo "$response" | tail -n1)

echo "HTTP状态码: $http_code"
if [ "$http_code" = "200" ]; then
    echo "✅ 看板页面加载正常"
else
    echo "❌ 看板页面加载失败"
    body=$(echo "$response" | head -n -1)
    echo "错误内容: $body"
fi

# 4. 创建测试草稿
echo -e "\n4. 创建测试草稿..."
test_draft_id="test_draft_$(date +%s)"
response=$(curl -s -w "\n%{http_code}" -X POST "$SERVER_URL/create_draft" \
  -H "Content-Type: application/json" \
  -d "{
    \"draft_id\": \"$test_draft_id\",
    \"width\": 1920,
    \"height\": 1080
  }")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n -1)

echo "HTTP状态码: $http_code"
if [ "$http_code" = "200" ]; then
    echo "✅ 测试草稿创建成功"
    echo "草稿ID: $test_draft_id"
    echo "响应内容:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo "❌ 测试草稿创建失败"
    echo "错误内容: $body"
fi

# 5. 再次测试草稿列表
echo -e "\n5. 再次测试草稿列表 (应该包含新创建的草稿)..."
response=$(curl -s -w "\n%{http_code}" "$SERVER_URL/api/drafts/list")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n -1)

echo "HTTP状态码: $http_code"
if [ "$http_code" = "200" ]; then
    echo "✅ 草稿列表获取成功"
    echo "响应内容:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo "❌ 草稿列表获取失败"
    echo "错误内容: $body"
fi

# 6. 检查数据库文件
echo -e "\n6. 检查数据库文件..."
if [ -f "/home/CapCutAPI-1.1.0/capcut.db" ]; then
    echo "✅ 数据库文件存在"
    echo "数据库文件大小: $(ls -lh /home/CapCutAPI-1.1.0/capcut.db | awk '{print $5}')"
else
    echo "❌ 数据库文件不存在"
fi

# 7. 检查服务状态
echo -e "\n7. 检查服务状态..."
if pgrep -f "capcut_server.py" > /dev/null; then
    echo "✅ CapCutAPI服务正在运行"
    echo "进程ID: $(pgrep -f 'capcut_server.py')"
else
    echo "❌ CapCutAPI服务未运行"
fi

echo -e "\n=== 测试完成 ==="