/**
 * WPS 一键打印脚本 v7 - 支持设计器模板
 * 参数: key=rowId  value=记录ID（从下拉选）
 * 
 * 使用方式：
 *   1. TEMPLATE_ID 留空 → 使用默认 ZPL 布局（由 /template-settings 配置参数）
 *   2. TEMPLATE_ID 填入模板ID → 使用设计器 /designer 保存的模板布局
 *   
 * 模板 ID 获取方式：
 *   打开 http://iot.klxzdh.com:8090/designer → 保存模板 → 
 *   在 data/templates/ 目录查看对应的 .json 文件名（不含扩展名）
 *   或访问 http://iot.klxzdh.com:8090/api/print/templates 查看模板列表
 */

var URL = 'http://iot.klxzdh.com/wps-api/print/wps';
var TOKEN = 'wps-print-token-2026';
var SHEET_NAME = '电控订单管理';

// ===== 第一张标签模板 =====
// 填入设计器模板ID，留空=默认布局
// '01b7ce76-6340-4236-80db-91e833325617' = "电控发货打印"
// '7fc18ad9-5861-4abb-ba25-291e95a399d8' = "图纸打印"
var TEMPLATE_ID = '7fc18ad9-5861-4abb-ba25-291e95a399d8';

// ===== 第二张标签模板 =====
// 留空=和第一张相同，填入不同ID=第二张用另一个模板
var TEMPLATE_ID_2 = '01b7ce76-6340-4236-80db-91e833325617';

// ===== 打印份数 =====
// 从表格哪个字段读取份数（使用已有的"数量"列）
var COPIES_FIELD = '数量';  // 表格中的"数量"字段值=打印份数
var DEFAULT_COPIES = 1;

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

  // 5. 排除特殊字段（不打印到标签上）
  var exclude = {};
  if (LABEL_TITLE_FIELD) exclude[LABEL_TITLE_FIELD] = true;
  if (BARCODE_FIELD) exclude[BARCODE_FIELD] = true;
  if (QRCODE_FIELD) exclude[QRCODE_FIELD] = true;
  if (PRINTER_FIELD) exclude[PRINTER_FIELD] = true;
  if (COPIES_FIELD) exclude[COPIES_FIELD] = true;

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

  // 7. 读取打印份数（从表格字段动态获取）
  var copies = DEFAULT_COPIES;
  if (COPIES_FIELD && fields[COPIES_FIELD] !== undefined && fields[COPIES_FIELD] !== null) {
    copies = Math.max(1, parseInt(fields[COPIES_FIELD]) || DEFAULT_COPIES);
  }

  // 构建第一张 payload
  var payload = {
    api_key: TOKEN,
    title: title,
    fields: printFields,
  };
  if (TEMPLATE_ID) payload.template_id = TEMPLATE_ID;
  if (barcode) payload.barcode = barcode;
  if (qrcode) payload.qrcode = qrcode;
  if (printer) payload.printer = printer;

  for (var i = 0; i < copies; i++) {
    HTTP.post(URL, payload);
  }

  // ============ 第二张标签（不同模板时） ============
  if (TEMPLATE_ID_2 && TEMPLATE_ID_2 !== TEMPLATE_ID) {
    var payload2 = {
      api_key: TOKEN,
      title: title,
      fields: printFields,
      template_id: TEMPLATE_ID_2,
    };
    if (barcode) payload2.barcode = barcode;
    if (qrcode) payload2.qrcode = qrcode;
    if (printer) payload2.printer = printer;
    for (var j = 0; j < copies; j++) {
      HTTP.post(URL, payload2);
    }
  }
  // ===============================================
}

main();
