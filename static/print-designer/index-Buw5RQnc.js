import { d as defineComponent, h, c as computed, o as onUnmounted, w as watch, s as shallowRef, l as loader, a as onMounted, n as nextTick, r as ref } from "./web-component-BlO1oYq8.js";
var __defProp$2 = Object.defineProperty;
var __defProps = Object.defineProperties;
var __getOwnPropDescs = Object.getOwnPropertyDescriptors;
var __getOwnPropSymbols$2 = Object.getOwnPropertySymbols;
var __hasOwnProp$2 = Object.prototype.hasOwnProperty;
var __propIsEnum$2 = Object.prototype.propertyIsEnumerable;
var __defNormalProp$2 = (obj, key, value) => key in obj ? __defProp$2(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __spreadValues$2 = (a, b) => {
  for (var prop in b || (b = {}))
    if (__hasOwnProp$2.call(b, prop))
      __defNormalProp$2(a, prop, b[prop]);
  if (__getOwnPropSymbols$2)
    for (var prop of __getOwnPropSymbols$2(b)) {
      if (__propIsEnum$2.call(b, prop))
        __defNormalProp$2(a, prop, b[prop]);
    }
  return a;
};
var __spreadProps = (a, b) => __defProps(a, __getOwnPropDescs(b));
const styles = {
  wrapper: {
    display: "flex",
    position: "relative",
    textAlign: "initial"
  },
  fullWidth: {
    width: "100%"
  },
  hide: {
    display: "none"
  }
};
function useContainer(props, isEditorReady) {
  const wrapperStyle = computed(() => {
    const { width, height } = props;
    return __spreadProps(__spreadValues$2({}, styles.wrapper), {
      width,
      height
    });
  });
  const containerStyle = computed(() => {
    return __spreadValues$2(__spreadValues$2({}, styles.fullWidth), !isEditorReady.value && styles.hide);
  });
  return { wrapperStyle, containerStyle };
}
function useMonaco() {
  const monacoRef = shallowRef(loader.__getMonacoInstance());
  const isLoadFailed = ref(false);
  let promise;
  onMounted(() => {
    if (monacoRef.value)
      return;
    promise = loader.init();
    promise.then((monacoInstance) => monacoRef.value = monacoInstance).catch((error) => {
      if ((error == null ? void 0 : error.type) !== "cancelation") {
        isLoadFailed.value = true;
        console.error("Monaco initialization error:", error);
      }
    });
  });
  const unload = () => promise == null ? void 0 : promise.cancel();
  return {
    monacoRef,
    unload,
    isLoadFailed
  };
}
function slotHelper(slot) {
  return typeof slot == "function" ? slot() : slot;
}
function isUndefined(v) {
  return v === void 0;
}
function getOrCreateModel(monaco, value, language, path) {
  return getModel(monaco, path) || createModel(monaco, value, language, path);
}
function getModel(monaco, path) {
  return monaco.editor.getModel(createModelUri(monaco, path));
}
function createModel(monaco, value, language, path) {
  return monaco.editor.createModel(value, language, path ? createModelUri(monaco, path) : void 0);
}
function createModelUri(monaco, path) {
  return monaco.Uri.parse(path);
}
var __defProp$1 = Object.defineProperty;
var __getOwnPropSymbols$1 = Object.getOwnPropertySymbols;
var __hasOwnProp$1 = Object.prototype.hasOwnProperty;
var __propIsEnum$1 = Object.prototype.propertyIsEnumerable;
var __defNormalProp$1 = (obj, key, value) => key in obj ? __defProp$1(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __spreadValues$1 = (a, b) => {
  for (var prop in b || (b = {}))
    if (__hasOwnProp$1.call(b, prop))
      __defNormalProp$1(a, prop, b[prop]);
  if (__getOwnPropSymbols$1)
    for (var prop of __getOwnPropSymbols$1(b)) {
      if (__propIsEnum$1.call(b, prop))
        __defNormalProp$1(a, prop, b[prop]);
    }
  return a;
};
const loadingStyle$1 = {
  display: "flex",
  height: "100%",
  width: "100%",
  justifyContent: "center",
  alignItems: "center"
};
var VueMonacoEditor = defineComponent({
  name: "VueMonacoEditor",
  // TODO: vue3 use modelValue, vue2 use value
  model: {
    prop: "value",
    event: "update:value"
  },
  props: {
    defaultValue: String,
    defaultPath: String,
    defaultLanguage: String,
    value: String,
    language: String,
    path: String,
    /* === */
    theme: {
      type: String,
      default: "vs"
    },
    line: Number,
    options: {
      type: Object,
      default: () => ({})
    },
    overrideServices: {
      type: Object,
      default: () => ({})
    },
    saveViewState: {
      type: Boolean,
      default: true
    },
    /* === */
    width: {
      type: [Number, String],
      default: "100%"
    },
    height: {
      type: [Number, String],
      default: "100%"
    },
    className: String
  },
  emits: ["update:value", "beforeMount", "mount", "change", "validate"],
  setup(props, ctx) {
    const viewStates = /* @__PURE__ */ new Map();
    const containerRef = shallowRef(null);
    const { monacoRef, unload, isLoadFailed } = useMonaco();
    const { editorRef } = useEditor(ctx, props, monacoRef, containerRef);
    const { disposeValidator } = useValidator(ctx, props, monacoRef, editorRef);
    const isEditorReady = computed(() => !!monacoRef.value && !!editorRef.value);
    const { wrapperStyle, containerStyle } = useContainer(props, isEditorReady);
    onUnmounted(() => {
      var _a, _b;
      (_a = disposeValidator.value) == null ? void 0 : _a.call(disposeValidator);
      if (editorRef.value) {
        (_b = editorRef.value.getModel()) == null ? void 0 : _b.dispose();
        editorRef.value.dispose();
      } else {
        unload();
      }
    });
    watch(
      [() => props.path, () => props.value, () => props.language, () => props.line],
      ([newPath, newValue, newLanguage, newLine], [oldPath, oldValue, oldLanguage, oldLine]) => {
        if (!isEditorReady.value) {
          return;
        }
        if (newPath !== oldPath) {
          const newModel = getOrCreateModel(
            monacoRef.value,
            newValue || props.defaultValue || "",
            newLanguage || props.defaultLanguage || "",
            newPath || props.defaultPath || ""
          );
          props.saveViewState && viewStates.set(oldPath, editorRef.value.saveViewState());
          editorRef.value.setModel(newModel);
          props.saveViewState && editorRef.value.restoreViewState(viewStates.get(newPath));
          if (!isUndefined(newLine)) {
            editorRef.value.revealLine(newLine);
          }
          return;
        }
        if (editorRef.value.getValue() !== newValue) {
          editorRef.value.setValue(newValue);
        }
        if (newLanguage !== oldLanguage) {
          monacoRef.value.editor.setModelLanguage(editorRef.value.getModel(), newLanguage);
        }
        if (!isUndefined(newLine) && newLine !== oldLine) {
          editorRef.value.revealLine(newLine);
        }
      }
    );
    watch(
      () => props.options,
      (options) => editorRef.value && editorRef.value.updateOptions(options),
      { deep: true }
    );
    watch(
      () => props.theme,
      (theme) => monacoRef.value && monacoRef.value.editor.setTheme(theme)
    );
    return {
      containerRef,
      isEditorReady,
      isLoadFailed,
      wrapperStyle,
      containerStyle
    };
  },
  render() {
    const {
      $slots,
      isEditorReady,
      isLoadFailed,
      wrapperStyle,
      containerStyle,
      // TODO: need remove, add `@deprecated` flag
      className
    } = this;
    return h(
      "div",
      {
        style: wrapperStyle
      },
      [
        !isEditorReady && h(
          "div",
          {
            style: loadingStyle$1
          },
          isLoadFailed ? $slots.failure ? slotHelper($slots.failure) : "load failed" : $slots.default ? slotHelper($slots.default) : "loading..."
        ),
        h("div", {
          ref: "containerRef",
          key: "monaco_editor_container",
          style: containerStyle,
          class: className
        })
      ]
    );
  }
});
function useEditor({ emit }, props, monacoRef, containerRef) {
  const editorRef = shallowRef(null);
  onMounted(() => {
    const stop = watch(
      monacoRef,
      () => {
        if (containerRef.value && monacoRef.value) {
          nextTick(() => stop());
          createEditor();
        }
      },
      { immediate: true }
    );
  });
  function createEditor() {
    var _a;
    if (!containerRef.value || !monacoRef.value || editorRef.value) {
      return;
    }
    emit("beforeMount", monacoRef.value);
    const autoCreatedModelPath = props.path || props.defaultPath;
    const defaultModel = getOrCreateModel(
      monacoRef.value,
      props.value || props.defaultValue || "",
      props.language || props.defaultLanguage || "",
      autoCreatedModelPath || ""
    );
    editorRef.value = monacoRef.value.editor.create(
      containerRef.value,
      __spreadValues$1({
        model: defaultModel,
        theme: props.theme,
        automaticLayout: true,
        autoIndent: "brackets",
        formatOnPaste: true,
        formatOnType: true
      }, props.options),
      props.overrideServices
    );
    (_a = editorRef.value) == null ? void 0 : _a.onDidChangeModelContent((event) => {
      const value = editorRef.value.getValue();
      if (value !== props.value) {
        emit("update:value", value);
        emit("change", value, event);
      }
    });
    if (editorRef.value && !isUndefined(props.line)) {
      editorRef.value.revealLine(props.line);
    }
    emit("mount", editorRef.value, monacoRef.value);
  }
  return { editorRef };
}
function useValidator({ emit }, props, monacoRef, editorRef) {
  const disposeValidator = ref(null);
  const stop = watch([monacoRef, editorRef], () => {
    if (monacoRef.value && editorRef.value) {
      nextTick(() => stop());
      const changeMarkersListener = monacoRef.value.editor.onDidChangeMarkers((uris) => {
        var _a, _b;
        const editorUri = (_b = (_a = editorRef.value) == null ? void 0 : _a.getModel()) == null ? void 0 : _b.uri;
        if (editorUri) {
          const currentEditorHasMarkerChanges = uris.find((uri) => uri.path === editorUri.path);
          if (currentEditorHasMarkerChanges) {
            const markers = monacoRef.value.editor.getModelMarkers({
              resource: editorUri
            });
            emit("validate", markers);
          }
        }
      });
      disposeValidator.value = () => changeMarkersListener == null ? void 0 : changeMarkersListener.dispose();
    }
  });
  return { disposeValidator };
}
export {
  VueMonacoEditor as Editor,
  VueMonacoEditor,
  VueMonacoEditor as default,
  loader,
  useMonaco
};
