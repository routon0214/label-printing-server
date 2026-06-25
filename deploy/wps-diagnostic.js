/**
 * 终极 HTTP 测试 - 只有一行请求
 */
function main() {
  HTTP.post('http://iot.klxzdh.com/api/print/wps', '{"title":"__DIAG__"}');
}
