/**
 * WPS 一键打印脚本 v8 - 打印机由本地代理决定
 * 参数: key=rowId  value=记录ID
 */

var URL = 'http://iot.klxzdh.com/wps-api/print/wps';
var TOKEN = 'wps-print-token-2026';
var SHEET_NAME = '电控订单管理';

// ===== 标签模板 =====
var TEMPLATE_ID = '7fc18ad9-5861-4abb-ba25-291e95a399d8';
var TEMPLATE_ID_2 = '01b7ce76-6340-4236-80db-91e833325617';

// ===== 打印份数 =====
var COPIES_FIELD = '数量';
var DEFAULT_COPIES = 1;

// ===== 标题 =====
var LABEL_TITLE_FIELD = '产品名称';
var LABEL_TITLE = '电控订单标签';
var BARCODE_FIELD = '订单编号';
var QRCODE_FIELD = '';

// ===== ⚠️ 打印机由本地代理决定，不再从表格读取 =====

function main() {
  // 0. 预先构建客户映射表（ID → 名称）和业务映射表
  var customerMap = {};
  var salesMap = {};
  try {
    var sheets = Application.Sheet.GetSheets();
    console.log('[DEBUG] 共找到 ' + sheets.length + ' 张表');
    // 查找客户信息表
    for (var si = 0; si < sheets.length; si++) {
      console.log('[DEBUG] 表名: ' + sheets[si].name);
      if (sheets[si].name === '客户信息') {
        var offset = undefined;
        while (true) {
          var params = { SheetId: sheets[si].id, PageSize: 200 };
          if (offset) params.Offset = offset;
          var res = Application.Record.GetRecords(params);
          if (!res || !res.records || res.records.length === 0) break;
          for (var j = 0; j < res.records.length; j++) {
            var r = res.records[j];
            var f = r.fields || {};
            var name = f['订货单位'] || f['客户名称'] || f['名称'] || '';
            if (r.id && name) customerMap[r.id] = String(name);
          }
          if (res.offset) { offset = res.offset; } else { break; }
        }
      }
      // 查找业务员/销售表
      if (sheets[si].name === '业务员' || sheets[si].name === '销售' || sheets[si].name === '销售人员') {
        var offset2 = undefined;
        while (true) {
          var params2 = { SheetId: sheets[si].id, PageSize: 200 };
          if (offset2) params2.Offset = offset2;
          var res2 = Application.Record.GetRecords(params2);
          if (!res2 || !res2.records || res2.records.length === 0) break;
          for (var k = 0; k < res2.records.length; k++) {
            var r2 = res2.records[k];
            var f2 = r2.fields || {};
            var name2 = f2['姓名'] || f2['名称'] || f2['业务员'] || '';
            if (r2.id && name2) salesMap[r2.id] = String(name2);
          }
          if (res2.offset) { offset2 = res2.offset; } else { break; }
        }
      }
    }
  } catch(e) {
    console.log('[DEBUG] 映射表构建出错: ' + e.message);
  }

  // 1. 获取记录ID
  var raw = Context.argv.rowId;
  var recordId = '';
  if (Array.isArray(raw)) {
    recordId = raw[0];
  } else {
    recordId = String(raw);
  }
  if (!recordId || recordId === 'undefined' || recordId === 'null') {
    throw new Error('缺少记录ID，参数选: key=rowId value=记录ID');
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
  if (COPIES_FIELD) exclude[COPIES_FIELD] = true;

  // 6. 提取打印字段（安全转换，避免 [object Object]）
  function toStr(v) {
    if (v === null || v === undefined) return '';
    if (typeof v === 'object' && v !== null) {
      console.log('[DEBUG toStr] type=' + (Array.isArray(v)?'array['+v.length+']':'object') + ' raw=' + JSON.stringify(v).substring(0,300));
    }
    if (typeof v === 'string') return v;
    if (typeof v === 'number' || typeof v === 'boolean') return String(v);
    if (Array.isArray(v)) {
      // 数组（多选关联字段）：取每个元素的 text/name/title
      var items = [];
      for (var i = 0; i < v.length; i++) {
        var item = v[i];
        if (typeof item === 'string') {
          items.push(item);
        } else if (typeof item === 'object' && item !== null) {
          items.push(item.text || item.name || item.title || extractString(item));
        }
      }
      return items.join('\n');
    }
    if (typeof v === 'object') {
      // 关联字段 (OneWayLink): 优先取 text/name/title
      if (v.text) return String(v.text);
      if (v.name) return String(v.name);
      if (v.title) return String(v.title);
      // 超链接字段
      if (v.address) return String(v.address);
      if (v.url) return String(v.url);
      if (v.link) return String(v.link);
      if (v.displayText) return String(v.displayText);
      // 回退
      return extractString(v);
    }
    return String(v);
  }

  // 通用对象→字符串提取
  function extractString(val) {
    if (val === null || val === undefined) return '';
    if (typeof val === 'string') return val;
    if (typeof val === 'number' || typeof val === 'boolean') return String(val);
    if (typeof val === 'object') {
      try { return JSON.stringify(val); } catch(e) { return ''; }
    }
    return String(val);
  }

	  // DEBUG: 查看仪表开孔打字原始数据
	  if (fields['仪表开孔打字'] !== undefined) {
	    var raw = fields['仪表开孔打字'];
	    console.log('[DEBUG 仪表开孔打字] typeof=' + typeof raw + ' isArray=' + Array.isArray(raw) + ' value=' + JSON.stringify(raw));
	  }

	  var printFields = [];
	  for (var key in fields) {
	    if (!fields.hasOwnProperty(key) || exclude[key]) continue;
	    var v = fields[key];
	    var strVal = toStr(v);
	    // 关联字段：用映射表翻译 ID→名称
	    if ((key === '客户名称' || key === '客户名') && strVal && customerMap[strVal]) {
	      console.log('[DEBUG] 客户名称映射: ' + strVal + ' → ' + customerMap[strVal]);
	      strVal = customerMap[strVal];
	    } else if (key === '客户名称' || key === '客户名') {
	      console.log('[DEBUG] 客户名称原始值: ' + JSON.stringify(v) + ' toStr结果: ' + strVal + ' 映射表有' + Object.keys(customerMap).length + '条');
	    }
	    if (key === '业务' && strVal && salesMap[strVal]) {
	      console.log('[DEBUG] 业务映射: ' + strVal + ' → ' + salesMap[strVal]);
	      strVal = salesMap[strVal];
	    } else if (key === '业务') {
	      console.log('[DEBUG] 业务原始值: ' + JSON.stringify(v) + ' toStr结果: ' + strVal + ' 映射表有' + Object.keys(salesMap).length + '条');
	    }
	    if (strVal !== '') {
      printFields.push({ label: key, value: strVal });
    }
  }

  if (printFields.length === 0) {
    throw new Error('未读取到任何有效字段');
  }

	  var barcode = toStr(BARCODE_FIELD ? fields[BARCODE_FIELD] : null);
  var qrcode = toStr(QRCODE_FIELD ? fields[QRCODE_FIELD] : null);

  // 7. 读取打印份数
  var copies = DEFAULT_COPIES;
  if (COPIES_FIELD && fields[COPIES_FIELD] !== undefined && fields[COPIES_FIELD] !== null) {
    copies = Math.max(1, parseInt(fields[COPIES_FIELD]) || DEFAULT_COPIES);
  }

  // 8. 构建 payload（不指定打印机，由本地代理决定）
  var payload = {
    api_key: TOKEN,
    title: title,
    fields: printFields,
  };
  if (TEMPLATE_ID) payload.template_id = TEMPLATE_ID;
  if (barcode) payload.barcode = barcode;
  if (qrcode) payload.qrcode = qrcode;

  for (var i = 0; i < copies; i++) {
    HTTP.post(URL, payload);
  }

  // ============ 第二张标签 ============
  if (TEMPLATE_ID_2 && TEMPLATE_ID_2 !== TEMPLATE_ID) {
    var payload2 = {
      api_key: TOKEN,
      title: title,
      fields: printFields,
      template_id: TEMPLATE_ID_2,
    };
    if (barcode) payload2.barcode = barcode;
    if (qrcode) payload2.qrcode = qrcode;
    for (var j = 0; j < copies; j++) {
      HTTP.post(URL, payload2);
    }
  }
}

main();
