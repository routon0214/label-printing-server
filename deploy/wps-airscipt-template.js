/**
 * WPS 一键打印脚本 v6 - 最终版
 * 参数: key=rowId  value=记录ID（从下拉选）
 */

var URL = 'http://iot.klxzdh.com/wps-api/print/wps';
var TOKEN = 'wps-print-token-2026';
var SHEET_NAME = '电控订单管理';

var AUTO_FIELDS = true;
var LABEL_TITLE_FIELD = '产品名称';
var LABEL_TITLE = '电控订单标签';
var BARCODE_FIELD = '订单编号';
var QRCODE_FIELD = '';
var FIXED_PRINTER = '';
var PRINTER_FIELD = '';

function main() {
  // 1. 获取记录ID（可能是数组或字符串）
  var raw = Context.argv.rowId;
  var recordId = '';
  if (Array.isArray(raw)) {
    recordId = raw[0];
  } else {
    recordId = String(raw);
  }
  if (!recordId || recordId === 'undefined' || recordId === 'null') {
    throw new Error('缺少记录ID，参数选: key=rowId  value=记录ID');
  }

  // 2. 查找工作表
  var sheets = Application.Sheet.GetSheets();
  var sheetId = null;
  for (var i = 0; i < sheets.length; i++) {
    if (sheets[i].name === SHEET_NAME) { sheetId = sheets[i].id; break; }
  }
  if (!sheetId) throw new Error('未找到工作表: ' + SHEET_NAME);

  // 3. 读目标记录
  var target = null;
  var offset = undefined;
  while (true) {
    var params = { SheetId: sheetId, PageSize: 100 };
    if (offset) params.Offset = offset;
    var res = Application.Record.GetRecords(params);
    if (!res || !res.records) break;
    for (var j = 0; j < res.records.length; j++) {
      if (res.records[j].id === recordId) { target = res.records[j]; break; }
    }
    if (target) break;
    if (res.offset) { offset = res.offset; } else { break; }
  }
  if (!target) throw new Error('未找到记录: ' + recordId);

  var fields = target.fields || {};

  // 4. 标题
  var title = LABEL_TITLE;
  if (LABEL_TITLE_FIELD && fields[LABEL_TITLE_FIELD]) {
    title = String(fields[LABEL_TITLE_FIELD]);
  }

  // 5. 排除特殊字段
  var exclude = {};
  if (LABEL_TITLE_FIELD) exclude[LABEL_TITLE_FIELD] = true;
  if (BARCODE_FIELD) exclude[BARCODE_FIELD] = true;
  if (QRCODE_FIELD) exclude[QRCODE_FIELD] = true;
  if (PRINTER_FIELD) exclude[PRINTER_FIELD] = true;

  // 6. 提取打印字段
  var printFields = [];
  for (var key in fields) {
    if (!fields.hasOwnProperty(key) || exclude[key]) continue;
    var v = fields[key];
    if (v !== null && v !== undefined && v !== '') {
      printFields.push({ label: key, value: String(v) });
    }
  }

  if (printFields.length === 0) {
    throw new Error('未读取到任何有效字段');
  }

  var barcode = (BARCODE_FIELD && fields[BARCODE_FIELD]) ? String(fields[BARCODE_FIELD]) : '';
  var qrcode = (QRCODE_FIELD && fields[QRCODE_FIELD]) ? String(fields[QRCODE_FIELD]) : '';
  var printer = FIXED_PRINTER;
  if (!printer && PRINTER_FIELD && fields[PRINTER_FIELD]) printer = String(fields[PRINTER_FIELD]);

  // 7. 发送
  var payload = {
    api_key: TOKEN,
    title: title,
    fields: printFields,
  };
  if (barcode) payload.barcode = barcode;
  if (qrcode) payload.qrcode = qrcode;
  if (printer) payload.printer = printer;

  HTTP.post(URL, payload);
}

main();
