// node_modules/@lit/reactive-element/css-tag.js
var t = globalThis;
var e = t.ShadowRoot && (void 0 === t.ShadyCSS || t.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype;
var s = Symbol();
var o = /* @__PURE__ */ new WeakMap();
var n = class {
  constructor(t5, e5, o5) {
    if (this._$cssResult$ = true, o5 !== s) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t5, this.t = e5;
  }
  get styleSheet() {
    let t5 = this.o;
    const s4 = this.t;
    if (e && void 0 === t5) {
      const e5 = void 0 !== s4 && 1 === s4.length;
      e5 && (t5 = o.get(s4)), void 0 === t5 && ((this.o = t5 = new CSSStyleSheet()).replaceSync(this.cssText), e5 && o.set(s4, t5));
    }
    return t5;
  }
  toString() {
    return this.cssText;
  }
};
var r = (t5) => new n("string" == typeof t5 ? t5 : t5 + "", void 0, s);
var i = (t5, ...e5) => {
  const o5 = 1 === t5.length ? t5[0] : e5.reduce((e6, s4, o6) => e6 + ((t6) => {
    if (true === t6._$cssResult$) return t6.cssText;
    if ("number" == typeof t6) return t6;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + t6 + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(s4) + t5[o6 + 1], t5[0]);
  return new n(o5, t5, s);
};
var S = (s4, o5) => {
  if (e) s4.adoptedStyleSheets = o5.map((t5) => t5 instanceof CSSStyleSheet ? t5 : t5.styleSheet);
  else for (const e5 of o5) {
    const o6 = document.createElement("style"), n4 = t.litNonce;
    void 0 !== n4 && o6.setAttribute("nonce", n4), o6.textContent = e5.cssText, s4.appendChild(o6);
  }
};
var c = e ? (t5) => t5 : (t5) => t5 instanceof CSSStyleSheet ? ((t6) => {
  let e5 = "";
  for (const s4 of t6.cssRules) e5 += s4.cssText;
  return r(e5);
})(t5) : t5;

// node_modules/@lit/reactive-element/reactive-element.js
var { is: i2, defineProperty: e2, getOwnPropertyDescriptor: h, getOwnPropertyNames: r2, getOwnPropertySymbols: o2, getPrototypeOf: n2 } = Object;
var a = globalThis;
var c2 = a.trustedTypes;
var l = c2 ? c2.emptyScript : "";
var p = a.reactiveElementPolyfillSupport;
var d = (t5, s4) => t5;
var u = { toAttribute(t5, s4) {
  switch (s4) {
    case Boolean:
      t5 = t5 ? l : null;
      break;
    case Object:
    case Array:
      t5 = null == t5 ? t5 : JSON.stringify(t5);
  }
  return t5;
}, fromAttribute(t5, s4) {
  let i6 = t5;
  switch (s4) {
    case Boolean:
      i6 = null !== t5;
      break;
    case Number:
      i6 = null === t5 ? null : Number(t5);
      break;
    case Object:
    case Array:
      try {
        i6 = JSON.parse(t5);
      } catch (t6) {
        i6 = null;
      }
  }
  return i6;
} };
var f = (t5, s4) => !i2(t5, s4);
var b = { attribute: true, type: String, converter: u, reflect: false, useDefault: false, hasChanged: f };
Symbol.metadata ??= Symbol("metadata"), a.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var y = class extends HTMLElement {
  static addInitializer(t5) {
    this._$Ei(), (this.l ??= []).push(t5);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t5, s4 = b) {
    if (s4.state && (s4.attribute = false), this._$Ei(), this.prototype.hasOwnProperty(t5) && ((s4 = Object.create(s4)).wrapped = true), this.elementProperties.set(t5, s4), !s4.noAccessor) {
      const i6 = Symbol(), h3 = this.getPropertyDescriptor(t5, i6, s4);
      void 0 !== h3 && e2(this.prototype, t5, h3);
    }
  }
  static getPropertyDescriptor(t5, s4, i6) {
    const { get: e5, set: r5 } = h(this.prototype, t5) ?? { get() {
      return this[s4];
    }, set(t6) {
      this[s4] = t6;
    } };
    return { get: e5, set(s5) {
      const h3 = e5?.call(this);
      r5?.call(this, s5), this.requestUpdate(t5, h3, i6);
    }, configurable: true, enumerable: true };
  }
  static getPropertyOptions(t5) {
    return this.elementProperties.get(t5) ?? b;
  }
  static _$Ei() {
    if (this.hasOwnProperty(d("elementProperties"))) return;
    const t5 = n2(this);
    t5.finalize(), void 0 !== t5.l && (this.l = [...t5.l]), this.elementProperties = new Map(t5.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(d("finalized"))) return;
    if (this.finalized = true, this._$Ei(), this.hasOwnProperty(d("properties"))) {
      const t6 = this.properties, s4 = [...r2(t6), ...o2(t6)];
      for (const i6 of s4) this.createProperty(i6, t6[i6]);
    }
    const t5 = this[Symbol.metadata];
    if (null !== t5) {
      const s4 = litPropertyMetadata.get(t5);
      if (void 0 !== s4) for (const [t6, i6] of s4) this.elementProperties.set(t6, i6);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t6, s4] of this.elementProperties) {
      const i6 = this._$Eu(t6, s4);
      void 0 !== i6 && this._$Eh.set(i6, t6);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(s4) {
    const i6 = [];
    if (Array.isArray(s4)) {
      const e5 = new Set(s4.flat(1 / 0).reverse());
      for (const s5 of e5) i6.unshift(c(s5));
    } else void 0 !== s4 && i6.push(c(s4));
    return i6;
  }
  static _$Eu(t5, s4) {
    const i6 = s4.attribute;
    return false === i6 ? void 0 : "string" == typeof i6 ? i6 : "string" == typeof t5 ? t5.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = false, this.hasUpdated = false, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    this._$ES = new Promise((t5) => this.enableUpdating = t5), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((t5) => t5(this));
  }
  addController(t5) {
    (this._$EO ??= /* @__PURE__ */ new Set()).add(t5), void 0 !== this.renderRoot && this.isConnected && t5.hostConnected?.();
  }
  removeController(t5) {
    this._$EO?.delete(t5);
  }
  _$E_() {
    const t5 = /* @__PURE__ */ new Map(), s4 = this.constructor.elementProperties;
    for (const i6 of s4.keys()) this.hasOwnProperty(i6) && (t5.set(i6, this[i6]), delete this[i6]);
    t5.size > 0 && (this._$Ep = t5);
  }
  createRenderRoot() {
    const t5 = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return S(t5, this.constructor.elementStyles), t5;
  }
  connectedCallback() {
    this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(true), this._$EO?.forEach((t5) => t5.hostConnected?.());
  }
  enableUpdating(t5) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((t5) => t5.hostDisconnected?.());
  }
  attributeChangedCallback(t5, s4, i6) {
    this._$AK(t5, i6);
  }
  _$ET(t5, s4) {
    const i6 = this.constructor.elementProperties.get(t5), e5 = this.constructor._$Eu(t5, i6);
    if (void 0 !== e5 && true === i6.reflect) {
      const h3 = (void 0 !== i6.converter?.toAttribute ? i6.converter : u).toAttribute(s4, i6.type);
      this._$Em = t5, null == h3 ? this.removeAttribute(e5) : this.setAttribute(e5, h3), this._$Em = null;
    }
  }
  _$AK(t5, s4) {
    const i6 = this.constructor, e5 = i6._$Eh.get(t5);
    if (void 0 !== e5 && this._$Em !== e5) {
      const t6 = i6.getPropertyOptions(e5), h3 = "function" == typeof t6.converter ? { fromAttribute: t6.converter } : void 0 !== t6.converter?.fromAttribute ? t6.converter : u;
      this._$Em = e5;
      const r5 = h3.fromAttribute(s4, t6.type);
      this[e5] = r5 ?? this._$Ej?.get(e5) ?? r5, this._$Em = null;
    }
  }
  requestUpdate(t5, s4, i6, e5 = false, h3) {
    if (void 0 !== t5) {
      const r5 = this.constructor;
      if (false === e5 && (h3 = this[t5]), i6 ??= r5.getPropertyOptions(t5), !((i6.hasChanged ?? f)(h3, s4) || i6.useDefault && i6.reflect && h3 === this._$Ej?.get(t5) && !this.hasAttribute(r5._$Eu(t5, i6)))) return;
      this.C(t5, s4, i6);
    }
    false === this.isUpdatePending && (this._$ES = this._$EP());
  }
  C(t5, s4, { useDefault: i6, reflect: e5, wrapped: h3 }, r5) {
    i6 && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(t5) && (this._$Ej.set(t5, r5 ?? s4 ?? this[t5]), true !== h3 || void 0 !== r5) || (this._$AL.has(t5) || (this.hasUpdated || i6 || (s4 = void 0), this._$AL.set(t5, s4)), true === e5 && this._$Em !== t5 && (this._$Eq ??= /* @__PURE__ */ new Set()).add(t5));
  }
  async _$EP() {
    this.isUpdatePending = true;
    try {
      await this._$ES;
    } catch (t6) {
      Promise.reject(t6);
    }
    const t5 = this.scheduleUpdate();
    return null != t5 && await t5, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ??= this.createRenderRoot(), this._$Ep) {
        for (const [t7, s5] of this._$Ep) this[t7] = s5;
        this._$Ep = void 0;
      }
      const t6 = this.constructor.elementProperties;
      if (t6.size > 0) for (const [s5, i6] of t6) {
        const { wrapped: t7 } = i6, e5 = this[s5];
        true !== t7 || this._$AL.has(s5) || void 0 === e5 || this.C(s5, void 0, i6, e5);
      }
    }
    let t5 = false;
    const s4 = this._$AL;
    try {
      t5 = this.shouldUpdate(s4), t5 ? (this.willUpdate(s4), this._$EO?.forEach((t6) => t6.hostUpdate?.()), this.update(s4)) : this._$EM();
    } catch (s5) {
      throw t5 = false, this._$EM(), s5;
    }
    t5 && this._$AE(s4);
  }
  willUpdate(t5) {
  }
  _$AE(t5) {
    this._$EO?.forEach((t6) => t6.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = true, this.firstUpdated(t5)), this.updated(t5);
  }
  _$EM() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = false;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$ES;
  }
  shouldUpdate(t5) {
    return true;
  }
  update(t5) {
    this._$Eq &&= this._$Eq.forEach((t6) => this._$ET(t6, this[t6])), this._$EM();
  }
  updated(t5) {
  }
  firstUpdated(t5) {
  }
};
y.elementStyles = [], y.shadowRootOptions = { mode: "open" }, y[d("elementProperties")] = /* @__PURE__ */ new Map(), y[d("finalized")] = /* @__PURE__ */ new Map(), p?.({ ReactiveElement: y }), (a.reactiveElementVersions ??= []).push("2.1.2");

// node_modules/lit-html/lit-html.js
var t2 = globalThis;
var i3 = (t5) => t5;
var s2 = t2.trustedTypes;
var e3 = s2 ? s2.createPolicy("lit-html", { createHTML: (t5) => t5 }) : void 0;
var h2 = "$lit$";
var o3 = `lit$${Math.random().toFixed(9).slice(2)}$`;
var n3 = "?" + o3;
var r3 = `<${n3}>`;
var l2 = document;
var c3 = () => l2.createComment("");
var a2 = (t5) => null === t5 || "object" != typeof t5 && "function" != typeof t5;
var u2 = Array.isArray;
var d2 = (t5) => u2(t5) || "function" == typeof t5?.[Symbol.iterator];
var f2 = "[ 	\n\f\r]";
var v = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g;
var _ = /-->/g;
var m = />/g;
var p2 = RegExp(`>|${f2}(?:([^\\s"'>=/]+)(${f2}*=${f2}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g");
var g = /'/g;
var $ = /"/g;
var y2 = /^(?:script|style|textarea|title)$/i;
var x = (t5) => (i6, ...s4) => ({ _$litType$: t5, strings: i6, values: s4 });
var b2 = x(1);
var w = x(2);
var T = x(3);
var E = Symbol.for("lit-noChange");
var A = Symbol.for("lit-nothing");
var C = /* @__PURE__ */ new WeakMap();
var P = l2.createTreeWalker(l2, 129);
function V(t5, i6) {
  if (!u2(t5) || !t5.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return void 0 !== e3 ? e3.createHTML(i6) : i6;
}
var N = (t5, i6) => {
  const s4 = t5.length - 1, e5 = [];
  let n4, l4 = 2 === i6 ? "<svg>" : 3 === i6 ? "<math>" : "", c4 = v;
  for (let i7 = 0; i7 < s4; i7++) {
    const s5 = t5[i7];
    let a3, u3, d3 = -1, f3 = 0;
    for (; f3 < s5.length && (c4.lastIndex = f3, u3 = c4.exec(s5), null !== u3); ) f3 = c4.lastIndex, c4 === v ? "!--" === u3[1] ? c4 = _ : void 0 !== u3[1] ? c4 = m : void 0 !== u3[2] ? (y2.test(u3[2]) && (n4 = RegExp("</" + u3[2], "g")), c4 = p2) : void 0 !== u3[3] && (c4 = p2) : c4 === p2 ? ">" === u3[0] ? (c4 = n4 ?? v, d3 = -1) : void 0 === u3[1] ? d3 = -2 : (d3 = c4.lastIndex - u3[2].length, a3 = u3[1], c4 = void 0 === u3[3] ? p2 : '"' === u3[3] ? $ : g) : c4 === $ || c4 === g ? c4 = p2 : c4 === _ || c4 === m ? c4 = v : (c4 = p2, n4 = void 0);
    const x2 = c4 === p2 && t5[i7 + 1].startsWith("/>") ? " " : "";
    l4 += c4 === v ? s5 + r3 : d3 >= 0 ? (e5.push(a3), s5.slice(0, d3) + h2 + s5.slice(d3) + o3 + x2) : s5 + o3 + (-2 === d3 ? i7 : x2);
  }
  return [V(t5, l4 + (t5[s4] || "<?>") + (2 === i6 ? "</svg>" : 3 === i6 ? "</math>" : "")), e5];
};
var S2 = class _S {
  constructor({ strings: t5, _$litType$: i6 }, e5) {
    let r5;
    this.parts = [];
    let l4 = 0, a3 = 0;
    const u3 = t5.length - 1, d3 = this.parts, [f3, v2] = N(t5, i6);
    if (this.el = _S.createElement(f3, e5), P.currentNode = this.el.content, 2 === i6 || 3 === i6) {
      const t6 = this.el.content.firstChild;
      t6.replaceWith(...t6.childNodes);
    }
    for (; null !== (r5 = P.nextNode()) && d3.length < u3; ) {
      if (1 === r5.nodeType) {
        if (r5.hasAttributes()) for (const t6 of r5.getAttributeNames()) if (t6.endsWith(h2)) {
          const i7 = v2[a3++], s4 = r5.getAttribute(t6).split(o3), e6 = /([.?@])?(.*)/.exec(i7);
          d3.push({ type: 1, index: l4, name: e6[2], strings: s4, ctor: "." === e6[1] ? I : "?" === e6[1] ? L : "@" === e6[1] ? z : H }), r5.removeAttribute(t6);
        } else t6.startsWith(o3) && (d3.push({ type: 6, index: l4 }), r5.removeAttribute(t6));
        if (y2.test(r5.tagName)) {
          const t6 = r5.textContent.split(o3), i7 = t6.length - 1;
          if (i7 > 0) {
            r5.textContent = s2 ? s2.emptyScript : "";
            for (let s4 = 0; s4 < i7; s4++) r5.append(t6[s4], c3()), P.nextNode(), d3.push({ type: 2, index: ++l4 });
            r5.append(t6[i7], c3());
          }
        }
      } else if (8 === r5.nodeType) if (r5.data === n3) d3.push({ type: 2, index: l4 });
      else {
        let t6 = -1;
        for (; -1 !== (t6 = r5.data.indexOf(o3, t6 + 1)); ) d3.push({ type: 7, index: l4 }), t6 += o3.length - 1;
      }
      l4++;
    }
  }
  static createElement(t5, i6) {
    const s4 = l2.createElement("template");
    return s4.innerHTML = t5, s4;
  }
};
function M(t5, i6, s4 = t5, e5) {
  if (i6 === E) return i6;
  let h3 = void 0 !== e5 ? s4._$Co?.[e5] : s4._$Cl;
  const o5 = a2(i6) ? void 0 : i6._$litDirective$;
  return h3?.constructor !== o5 && (h3?._$AO?.(false), void 0 === o5 ? h3 = void 0 : (h3 = new o5(t5), h3._$AT(t5, s4, e5)), void 0 !== e5 ? (s4._$Co ??= [])[e5] = h3 : s4._$Cl = h3), void 0 !== h3 && (i6 = M(t5, h3._$AS(t5, i6.values), h3, e5)), i6;
}
var R = class {
  constructor(t5, i6) {
    this._$AV = [], this._$AN = void 0, this._$AD = t5, this._$AM = i6;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t5) {
    const { el: { content: i6 }, parts: s4 } = this._$AD, e5 = (t5?.creationScope ?? l2).importNode(i6, true);
    P.currentNode = e5;
    let h3 = P.nextNode(), o5 = 0, n4 = 0, r5 = s4[0];
    for (; void 0 !== r5; ) {
      if (o5 === r5.index) {
        let i7;
        2 === r5.type ? i7 = new k(h3, h3.nextSibling, this, t5) : 1 === r5.type ? i7 = new r5.ctor(h3, r5.name, r5.strings, this, t5) : 6 === r5.type && (i7 = new Z(h3, this, t5)), this._$AV.push(i7), r5 = s4[++n4];
      }
      o5 !== r5?.index && (h3 = P.nextNode(), o5++);
    }
    return P.currentNode = l2, e5;
  }
  p(t5) {
    let i6 = 0;
    for (const s4 of this._$AV) void 0 !== s4 && (void 0 !== s4.strings ? (s4._$AI(t5, s4, i6), i6 += s4.strings.length - 2) : s4._$AI(t5[i6])), i6++;
  }
};
var k = class _k {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(t5, i6, s4, e5) {
    this.type = 2, this._$AH = A, this._$AN = void 0, this._$AA = t5, this._$AB = i6, this._$AM = s4, this.options = e5, this._$Cv = e5?.isConnected ?? true;
  }
  get parentNode() {
    let t5 = this._$AA.parentNode;
    const i6 = this._$AM;
    return void 0 !== i6 && 11 === t5?.nodeType && (t5 = i6.parentNode), t5;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t5, i6 = this) {
    t5 = M(this, t5, i6), a2(t5) ? t5 === A || null == t5 || "" === t5 ? (this._$AH !== A && this._$AR(), this._$AH = A) : t5 !== this._$AH && t5 !== E && this._(t5) : void 0 !== t5._$litType$ ? this.$(t5) : void 0 !== t5.nodeType ? this.T(t5) : d2(t5) ? this.k(t5) : this._(t5);
  }
  O(t5) {
    return this._$AA.parentNode.insertBefore(t5, this._$AB);
  }
  T(t5) {
    this._$AH !== t5 && (this._$AR(), this._$AH = this.O(t5));
  }
  _(t5) {
    this._$AH !== A && a2(this._$AH) ? this._$AA.nextSibling.data = t5 : this.T(l2.createTextNode(t5)), this._$AH = t5;
  }
  $(t5) {
    const { values: i6, _$litType$: s4 } = t5, e5 = "number" == typeof s4 ? this._$AC(t5) : (void 0 === s4.el && (s4.el = S2.createElement(V(s4.h, s4.h[0]), this.options)), s4);
    if (this._$AH?._$AD === e5) this._$AH.p(i6);
    else {
      const t6 = new R(e5, this), s5 = t6.u(this.options);
      t6.p(i6), this.T(s5), this._$AH = t6;
    }
  }
  _$AC(t5) {
    let i6 = C.get(t5.strings);
    return void 0 === i6 && C.set(t5.strings, i6 = new S2(t5)), i6;
  }
  k(t5) {
    u2(this._$AH) || (this._$AH = [], this._$AR());
    const i6 = this._$AH;
    let s4, e5 = 0;
    for (const h3 of t5) e5 === i6.length ? i6.push(s4 = new _k(this.O(c3()), this.O(c3()), this, this.options)) : s4 = i6[e5], s4._$AI(h3), e5++;
    e5 < i6.length && (this._$AR(s4 && s4._$AB.nextSibling, e5), i6.length = e5);
  }
  _$AR(t5 = this._$AA.nextSibling, s4) {
    for (this._$AP?.(false, true, s4); t5 !== this._$AB; ) {
      const s5 = i3(t5).nextSibling;
      i3(t5).remove(), t5 = s5;
    }
  }
  setConnected(t5) {
    void 0 === this._$AM && (this._$Cv = t5, this._$AP?.(t5));
  }
};
var H = class {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t5, i6, s4, e5, h3) {
    this.type = 1, this._$AH = A, this._$AN = void 0, this.element = t5, this.name = i6, this._$AM = e5, this.options = h3, s4.length > 2 || "" !== s4[0] || "" !== s4[1] ? (this._$AH = Array(s4.length - 1).fill(new String()), this.strings = s4) : this._$AH = A;
  }
  _$AI(t5, i6 = this, s4, e5) {
    const h3 = this.strings;
    let o5 = false;
    if (void 0 === h3) t5 = M(this, t5, i6, 0), o5 = !a2(t5) || t5 !== this._$AH && t5 !== E, o5 && (this._$AH = t5);
    else {
      const e6 = t5;
      let n4, r5;
      for (t5 = h3[0], n4 = 0; n4 < h3.length - 1; n4++) r5 = M(this, e6[s4 + n4], i6, n4), r5 === E && (r5 = this._$AH[n4]), o5 ||= !a2(r5) || r5 !== this._$AH[n4], r5 === A ? t5 = A : t5 !== A && (t5 += (r5 ?? "") + h3[n4 + 1]), this._$AH[n4] = r5;
    }
    o5 && !e5 && this.j(t5);
  }
  j(t5) {
    t5 === A ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t5 ?? "");
  }
};
var I = class extends H {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t5) {
    this.element[this.name] = t5 === A ? void 0 : t5;
  }
};
var L = class extends H {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t5) {
    this.element.toggleAttribute(this.name, !!t5 && t5 !== A);
  }
};
var z = class extends H {
  constructor(t5, i6, s4, e5, h3) {
    super(t5, i6, s4, e5, h3), this.type = 5;
  }
  _$AI(t5, i6 = this) {
    if ((t5 = M(this, t5, i6, 0) ?? A) === E) return;
    const s4 = this._$AH, e5 = t5 === A && s4 !== A || t5.capture !== s4.capture || t5.once !== s4.once || t5.passive !== s4.passive, h3 = t5 !== A && (s4 === A || e5);
    e5 && this.element.removeEventListener(this.name, this, s4), h3 && this.element.addEventListener(this.name, this, t5), this._$AH = t5;
  }
  handleEvent(t5) {
    "function" == typeof this._$AH ? this._$AH.call(this.options?.host ?? this.element, t5) : this._$AH.handleEvent(t5);
  }
};
var Z = class {
  constructor(t5, i6, s4) {
    this.element = t5, this.type = 6, this._$AN = void 0, this._$AM = i6, this.options = s4;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t5) {
    M(this, t5);
  }
};
var j = { M: h2, P: o3, A: n3, C: 1, L: N, R, D: d2, V: M, I: k, H, N: L, U: z, B: I, F: Z };
var B = t2.litHtmlPolyfillSupport;
B?.(S2, k), (t2.litHtmlVersions ??= []).push("3.3.3");
var D = (t5, i6, s4) => {
  const e5 = s4?.renderBefore ?? i6;
  let h3 = e5._$litPart$;
  if (void 0 === h3) {
    const t6 = s4?.renderBefore ?? null;
    e5._$litPart$ = h3 = new k(i6.insertBefore(c3(), t6), t6, void 0, s4 ?? {});
  }
  return h3._$AI(t5), h3;
};

// node_modules/lit-element/lit-element.js
var s3 = globalThis;
var i4 = class extends y {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const t5 = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= t5.firstChild, t5;
  }
  update(t5) {
    const r5 = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t5), this._$Do = D(r5, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(true);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(false);
  }
  render() {
    return E;
  }
};
i4._$litElement$ = true, i4["finalized"] = true, s3.litElementHydrateSupport?.({ LitElement: i4 });
var o4 = s3.litElementPolyfillSupport;
o4?.({ LitElement: i4 });
(s3.litElementVersions ??= []).push("4.2.2");

// src/api/rooms.ts
function subscribeRooms(hass, onRooms) {
  return hass.connection.subscribeMessage(
    (message) => onRooms(message.rooms),
    { type: "hyggely/rooms/subscribe" }
  );
}
function returnToAuto(hass, roomId) {
  return hass.callWS({
    type: "hyggely/room/return_to_auto",
    room_id: roomId
  });
}

// src/api/levels.ts
function getRoomLevels(hass, roomId) {
  return hass.callWS({ type: "hyggely/room/levels", room_id: roomId });
}
function setRoomLevels(hass, roomId, changes) {
  return hass.callWS({
    type: "hyggely/room/set_levels",
    room_id: roomId,
    ...changes
  });
}
function getGlobalTemperatures(hass) {
  return hass.callWS({ type: "hyggely/house/temperatures" });
}
function setGlobalTemperatures(hass, changes) {
  return hass.callWS({ type: "hyggely/house/set_temperatures", ...changes });
}

// src/i18n.ts
function language(hass) {
  return hass?.locale?.language ?? hass?.language ?? "en";
}
function localize(hass, texts) {
  return language(hass).startsWith("de") ? texts.de : texts.en;
}
function format(text, values) {
  return text.replace(/\{(\w+)\}/g, (match, key) => values[key] ?? match);
}
function errorMessage(error) {
  const message = error?.message;
  return typeof message === "string" ? message : String(error);
}
function formatTemperature(hass, value) {
  if (value === null || value === void 0) {
    return "– °C";
  }
  const number = new Intl.NumberFormat(language(hass), {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  }).format(value);
  return `${number} °C`;
}

// src/stepper.ts
var MIN_TEMPERATURE = 5;
var MAX_TEMPERATURE = 25;
var LEAD_TIME_STEP_MINUTES = 15;
var MAX_LEAD_TIME_MINUTES = 180;
var SAVE_DELAY_MS = 1e3;
function stepTemperature(value, direction) {
  const next = direction > 0 ? Math.floor(value) + 1 : Math.ceil(value) - 1;
  return Math.min(MAX_TEMPERATURE, Math.max(MIN_TEMPERATURE, next));
}
function stepLeadTime(minutes2, direction) {
  const steps = minutes2 / LEAD_TIME_STEP_MINUTES;
  const next = (direction > 0 ? Math.floor(steps) + 1 : Math.ceil(steps) - 1) * LEAD_TIME_STEP_MINUTES;
  return Math.min(MAX_LEAD_TIME_MINUTES, Math.max(0, next));
}
function stepper(options) {
  return b2`<div class="row">
    <span class="row-name">${options.label}</span>
    <span class="stepper">
      <button aria-label=${options.less} ?disabled=${!options.canDown} @click=${() => options.onStep(-1)}>−</button>
      <span class="value">${options.value}</span>
      <button aria-label=${options.more} ?disabled=${!options.canUp} @click=${() => options.onStep(1)}>+</button>
    </span>
  </div>`;
}
var stepperStyles = i`
  .row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    padding: 5px 0;
  }
  .row-name {
    display: flex;
    align-items: center;
  }
  .stepper {
    display: inline-flex;
    align-items: center;
    border: 1px solid var(--cc-divider);
    border-radius: 10px;
    overflow: hidden;
  }
  .stepper button {
    width: 44px;
    height: 40px;
    border: 0;
    background: transparent;
    color: var(--cc-primary);
    font: inherit;
    font-size: 20px;
    line-height: 1;
    cursor: pointer;
  }
  .stepper button:disabled {
    color: var(--cc-muted);
    opacity: 0.35;
    cursor: default;
  }
  .stepper .value {
    min-width: 84px;
    text-align: center;
    font-variant-numeric: tabular-nums;
  }
  .hint {
    margin: 8px 0 0;
    color: var(--warning-color, #e65100);
  }
  .error {
    margin: 8px 0 0;
    color: var(--error-color, #d32f2f);
  }
`;
var DelayedSave = class {
  constructor(_send) {
    this._send = _send;
    this._changes = {};
    this.flush = () => {
      window.clearTimeout(this._timer);
      this._timer = void 0;
      const changes = this._changes;
      if (Object.keys(changes).length === 0) {
        return;
      }
      this._changes = {};
      this._send(changes);
    };
    this._flushWhenHidden = () => {
      if (document.visibilityState === "hidden") {
        this.flush();
      }
    };
  }
  get changes() {
    return this._changes;
  }
  change(changes) {
    this._changes = { ...this._changes, ...changes };
    window.clearTimeout(this._timer);
    this._timer = window.setTimeout(this.flush, SAVE_DELAY_MS);
  }
  connect() {
    document.addEventListener("visibilitychange", this._flushWhenHidden);
    window.addEventListener("pagehide", this.flush);
  }
  disconnect() {
    document.removeEventListener("visibilitychange", this._flushWhenHidden);
    window.removeEventListener("pagehide", this.flush);
    this.flush();
  }
};

// src/styles.ts
var sharedStyles = i`
  :host {
    --cc-auto: var(--state-climate-auto-color, #2e7d32);
    --cc-heat: var(--state-climate-heat-color, #e65100);
    --cc-off: var(--state-climate-off-color, #757575);
    --cc-frost: #4fc3f7;
    --cc-night: #5c6bc0;
    --cc-muted: var(--secondary-text-color, #6f6f6f);
    --cc-divider: var(--divider-color, rgba(0, 0, 0, 0.12));
    --cc-card: var(--card-background-color, #fff);
    --cc-primary: var(--primary-color, #03a9f4);
  }
  .card {
    background: var(--cc-card);
    border: 1px solid var(--cc-divider);
    border-radius: var(--ha-card-border-radius, 12px);
    margin-bottom: 12px;
  }
  .pad {
    padding: 14px;
  }
  .muted {
    color: var(--cc-muted);
  }
  .small {
    font-size: 13px;
  }
  h2.section {
    font-size: 15px;
    font-weight: 600;
    color: var(--cc-muted);
    margin: 20px 2px 8px;
  }
  .chips {
    display: flex;
    gap: 6px;
    overflow-x: auto;
    padding-bottom: 6px;
    margin-bottom: 6px;
  }
  .chip {
    border: 1px solid var(--cc-divider);
    border-radius: 16px;
    padding: 6px 12px;
    background: var(--cc-card);
    color: var(--primary-text-color);
    font: inherit;
    font-size: 14px;
    white-space: nowrap;
    cursor: pointer;
  }
  .chip.selected {
    background: var(--cc-primary);
    border-color: transparent;
    color: var(--text-primary-color, #fff);
  }
`;

// src/define.ts
function defineOnce(name, element) {
  if (!customElements.get(name)) {
    customElements.define(name, element);
  }
}

// src/house/global-temperatures-section.ts
var TEXTS = {
  de: {
    title: "Temperaturen für das ganze Haus",
    away: "Abwesend",
    vacation: "Urlaub",
    frost: "Frostschutz",
    frostNote: "Frostschutz gilt bei offenem Fenster, bei „Aus“ und wenn das Haus aus ist.",
    less: "{name} weniger",
    more: "{name} mehr",
    loading: "Lade Temperaturen …",
    failed: "Konnte nicht gespeichert werden: {error}",
    loadFailed: "Temperaturen konnten nicht geladen werden: {error}"
  },
  en: {
    title: "Temperatures for the whole house",
    away: "Away",
    vacation: "Vacation",
    frost: "Frost protection",
    frostNote: "Frost protection applies with a window open, in “Off” and when the house is off.",
    less: "{name} lower",
    more: "{name} higher",
    loading: "Loading temperatures …",
    failed: "Could not be saved: {error}",
    loadFailed: "Temperatures could not be loaded: {error}"
  }
};
var GLOBAL_LEVELS = ["away", "vacation", "frost"];
var GlobalTemperaturesSection = class extends i4 {
  constructor() {
    super(...arguments);
    this._loading = false;
    this._save = new DelayedSave((changes) => this._send(changes));
  }
  connectedCallback() {
    super.connectedCallback();
    this._save.connect();
  }
  disconnectedCallback() {
    this._save.disconnect();
    super.disconnectedCallback();
  }
  willUpdate(changed) {
    if (changed.has("hass") && !this._temperatures && !this._loading) {
      this._load();
    }
  }
  _load() {
    if (!this.hass) {
      return;
    }
    this._loading = true;
    getGlobalTemperatures(this.hass).then((temperatures) => {
      this._temperatures = temperatures;
      this._error = void 0;
    }).catch((error) => {
      this._error = format(localize(this.hass, TEXTS).loadFailed, { error: errorMessage(error) });
    }).finally(() => {
      this._loading = false;
    });
  }
  _send(changes) {
    if (!this.hass) {
      return;
    }
    if (this._temperatures) {
      this._temperatures = { ...this._temperatures, ...changes };
    }
    setGlobalTemperatures(this.hass, changes).catch((error) => {
      this._temperatures = void 0;
      this._load();
      this._error = format(localize(this.hass, TEXTS).failed, { error: errorMessage(error) });
    });
  }
  render() {
    const t5 = localize(this.hass, TEXTS);
    return b2`<h2 class="section">${t5.title}</h2>
      <div class="card pad">${this._body(t5)}</div>`;
  }
  _body(t5) {
    if (!this._temperatures) {
      return this._error ? b2`<p class="error" role="alert">${this._error}</p>` : b2`<span class="muted small">${t5.loading}</span>`;
    }
    const temperatures = { ...this._temperatures, ...this._save.changes };
    return b2`
      ${GLOBAL_LEVELS.map((level) => {
      const key = `${level}_temperature`;
      const value = temperatures[key];
      return stepper({
        label: t5[level],
        value: formatTemperature(this.hass, value),
        less: format(t5.less, { name: t5[level] }),
        more: format(t5.more, { name: t5[level] }),
        canDown: value > MIN_TEMPERATURE,
        canUp: value < MAX_TEMPERATURE,
        onStep: (direction) => {
          this._error = void 0;
          this._save.change({ [key]: stepTemperature(value, direction) });
          this.requestUpdate();
        }
      });
    })}
      <p class="muted small">${t5.frostNote}</p>
      ${this._error ? b2`<p class="error small" role="alert">${this._error}</p>` : A}
    `;
  }
};
GlobalTemperaturesSection.properties = {
  hass: { attribute: false },
  _temperatures: { state: true },
  _error: { state: true }
};
GlobalTemperaturesSection.styles = [sharedStyles, stepperStyles];
defineOnce("cc-global-temperatures-section", GlobalTemperaturesSection);

// src/api/house.ts
function subscribeHouse(hass, onHouse) {
  return hass.connection.subscribeMessage(onHouse, {
    type: "hyggely/house/subscribe"
  });
}
function setHouseMode(hass, houseMode) {
  return hass.callWS({ type: "hyggely/house/set_mode", house_mode: houseMode });
}
function startVacation(hass, end) {
  return hass.callWS({ type: "hyggely/house/start_vacation", end });
}
var VACATION_END_MUST_BE_AHEAD = "vacation_end_must_be_ahead";
function formatVacationEnd(language2, vacationEnd) {
  const [date, time] = vacationEnd.slice(0, 16).split("T");
  const [year, month, day] = date.split("-").map(Number);
  const [hour, minute] = time.split(":").map(Number);
  return new Intl.DateTimeFormat(language2, {
    timeZone: "UTC",
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(Date.UTC(year, month - 1, day, hour, minute)));
}

// src/house/house-mode-section.ts
var DEFAULT_VACATION_DAYS = 7;
var DEFAULT_VACATION_END_TIME = "18:00";
var TEXTS2 = {
  de: {
    title: "Hausbetriebsart",
    auto: "Automatik",
    vacation: "Urlaub",
    off: "Aus",
    explainAuto: "Alle Räume folgen ihrem Zeitplan.",
    explainVacation: "Alle Räume halten die Urlaubstemperatur. Zum Urlaubsende geht das Haus von selbst zurück auf Automatik.",
    explainOff: "Alle Räume halten Frostschutz.",
    overrideStillWorks: "Eine manuelle Übersteuerung wirkt trotzdem.",
    vacationUntil: "Urlaub bis",
    thenAuto: ", danach Automatik.",
    changeEnd: "Ende ändern",
    sheetStart: "Urlaub",
    sheetChange: "Urlaubsende ändern",
    sheetHint: "Bis zum Ende halten alle Räume die Urlaubstemperatur, danach Automatik.",
    endDate: "Urlaub endet am",
    endTime: "um",
    start: "Urlaub starten",
    save: "Speichern",
    cancel: "Abbrechen",
    endNotAhead: "Das Urlaubsende muss in der Zukunft liegen.",
    failed: "Die Heizungssteuerung hat abgelehnt: ",
    awayTitle: "Abwesend",
    yes: "Ja",
    no: "Nein",
    awayNow: "Niemand ist zu Hause. Räume ohne Übersteuerung halten die Abwesend-Temperatur.",
    notAway: "Mindestens eine Person ist zu Hause.",
    awayExplain: "Abwesend ist keine Hausbetriebsart, sondern folgt aus der Anwesenheit: alle Personen länger als die Abwesenheitsverzögerung weg.",
    noPersons: "Keine Personen eingerichtet, Abwesend wirkt nie. Personen legst du in den Optionen der Integration fest.",
    home: "zu Hause",
    not_home: "unterwegs",
    unknown: "unbekannt – zählt als zu Hause",
    loading: "Lade Haus …"
  },
  en: {
    title: "House mode",
    auto: "Automatic",
    vacation: "Vacation",
    off: "Off",
    explainAuto: "All rooms follow their schedule.",
    explainVacation: "All rooms hold the vacation temperature. At the vacation end the house returns to automatic by itself.",
    explainOff: "All rooms hold frost protection.",
    overrideStillWorks: "A manual override still works.",
    vacationUntil: "Vacation until",
    thenAuto: ", then automatic.",
    changeEnd: "Change end",
    sheetStart: "Vacation",
    sheetChange: "Change vacation end",
    sheetHint: "Until the end all rooms hold the vacation temperature, then automatic.",
    endDate: "Vacation ends on",
    endTime: "at",
    start: "Start vacation",
    save: "Save",
    cancel: "Cancel",
    endNotAhead: "The vacation end must be in the future.",
    failed: "The heating control refused: ",
    awayTitle: "Away",
    yes: "Yes",
    no: "No",
    awayNow: "Nobody is home. Rooms without an override hold the away temperature.",
    notAway: "At least one person is home.",
    awayExplain: "Away is not a house mode; it follows from presence: all persons gone for longer than the presence delay.",
    noPersons: "No persons set up, so the house is never away. Choose persons in the options of the integration.",
    home: "home",
    not_home: "away",
    unknown: "unknown – counts as home",
    loading: "Loading house …"
  }
};
var MODES = ["auto", "vacation", "off"];
function pad(value) {
  return String(value).padStart(2, "0");
}
function suggestedEnd(house) {
  if (house.vacation_end && new Date(house.vacation_end).getTime() > Date.now()) {
    const [date, time] = house.vacation_end.slice(0, 16).split("T");
    return { date, time };
  }
  const day = /* @__PURE__ */ new Date();
  day.setDate(day.getDate() + DEFAULT_VACATION_DAYS);
  return {
    date: `${day.getFullYear()}-${pad(day.getMonth() + 1)}-${pad(day.getDate())}`,
    time: DEFAULT_VACATION_END_TIME
  };
}
var HouseModeSection = class extends i4 {
  constructor() {
    super(...arguments);
    this._openSheet = () => {
      if (this._house) {
        this._sheet = { ...suggestedEnd(this._house), busy: false };
      }
    };
    this._closeSheet = () => {
      this._sheet = void 0;
    };
    this._submitSheet = async () => {
      const sheet = this._sheet;
      if (!this.hass || !sheet) {
        return;
      }
      const t5 = localize(this.hass, TEXTS2);
      this._sheet = { ...sheet, busy: true, error: void 0 };
      try {
        await startVacation(this.hass, `${sheet.date}T${sheet.time}`);
        this._sheet = void 0;
      } catch (error) {
        const code = error?.code;
        this._sheet = {
          ...sheet,
          busy: false,
          error: code === VACATION_END_MUST_BE_AHEAD ? t5.endNotAhead : t5.failed + errorMessage(error)
        };
      }
    };
  }
  connectedCallback() {
    super.connectedCallback();
    this._subscribe();
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    this._unsubscribe?.then((unsubscribe) => unsubscribe()).catch(() => void 0);
    this._unsubscribe = void 0;
  }
  updated(changed) {
    if (changed.has("hass")) {
      this._subscribe();
    }
  }
  _subscribe() {
    if (!this.hass || !this.isConnected || this._unsubscribe) {
      return;
    }
    this._unsubscribe = subscribeHouse(this.hass, (house) => this._house = house);
    this._unsubscribe.catch((error) => {
      this._unsubscribe = void 0;
      this._error = errorMessage(error);
    });
  }
  render() {
    const t5 = localize(this.hass, TEXTS2);
    const house = this._house;
    if (!house) {
      return b2`<h2 class="section">${t5.title}</h2>
        <div class="card pad muted small">${this._error ?? t5.loading}</div>`;
    }
    return b2`
      <h2 class="section">${t5.title}</h2>
      ${this._modeCard(house, t5)} ${this._awayCard(house, t5)} ${this._vacationSheet(house, t5)}
    `;
  }
  _modeCard(house, t5) {
    const explain = {
      auto: t5.explainAuto,
      vacation: t5.explainVacation,
      off: t5.explainOff
    }[house.house_mode];
    return b2`<div class="card pad">
      <div class="seg" role="group" aria-label=${t5.title}>
        ${MODES.map(
      (mode) => b2`<button
            class=${house.house_mode === mode ? "on" : ""}
            aria-pressed=${house.house_mode === mode ? "true" : "false"}
            @click=${() => this._choose(mode)}
          >
            ${t5[mode]}
          </button>`
    )}
      </div>
      <p class="muted small">${explain} ${t5.overrideStillWorks}</p>
      ${house.house_mode === "vacation" && house.vacation_end ? b2`<div class="row-between">
            <span
              >${t5.vacationUntil}
              <b>${formatVacationEnd(language(this.hass), house.vacation_end)}</b>${t5.thenAuto}</span
            >
            <button class="btn" @click=${this._openSheet}>${t5.changeEnd}</button>
          </div>` : A}
      ${this._error ? b2`<p class="err" role="alert">${this._error}</p>` : A}
    </div>`;
  }
  _awayCard(house, t5) {
    return b2`<div class="card pad">
      <div class="row-between">
        <b>${t5.awayTitle}</b>
        <span class="chip static ${house.away ? "selected warn" : ""}">
          ${house.away ? t5.yes : t5.no}
        </span>
      </div>
      <p class="muted small">${house.away ? t5.awayNow : t5.notAway} ${t5.awayExplain}</p>
      ${house.persons.length === 0 ? b2`<p class="muted small">${t5.noPersons}</p>` : b2`<ul class="persons">
            ${house.persons.map(
      (person) => b2`<li>
                <span>${person.name}</span>
                <span class="presence presence-${person.presence}"
                  >${t5[person.presence]}</span
                >
              </li>`
    )}
          </ul>`}
    </div>`;
  }
  _vacationSheet(house, t5) {
    const sheet = this._sheet;
    if (!sheet) {
      return A;
    }
    const onVacation = house.house_mode === "vacation";
    return b2`<div class="sheet-root">
      <div class="backdrop" @click=${this._closeSheet}></div>
      <div class="sheet" role="dialog" aria-modal="true" aria-labelledby="sheet-title">
        <h3 id="sheet-title">${onVacation ? t5.sheetChange : t5.sheetStart}</h3>
        <p class="muted small">${t5.sheetHint}</p>
        <div class="field-row">
          <label
            >${t5.endDate}
            <input
              type="date"
              .value=${sheet.date}
              @input=${(event) => this._editSheet({ date: event.target.value })}
          /></label>
          <label
            >${t5.endTime}
            <input
              type="time"
              .value=${sheet.time}
              @input=${(event) => this._editSheet({ time: event.target.value })}
          /></label>
        </div>
        ${sheet.error ? b2`<p class="err" role="alert">${sheet.error}</p>` : A}
        <div class="sheet-actions">
          <span class="spacer"></span>
          <button class="btn" @click=${this._closeSheet}>${t5.cancel}</button>
          <button
            class="btn primary"
            ?disabled=${sheet.busy || !sheet.date || !sheet.time}
            @click=${this._submitSheet}
          >
            ${onVacation ? t5.save : t5.start}
          </button>
        </div>
      </div>
    </div>`;
  }
  _choose(mode) {
    const house = this._house;
    if (!this.hass || !house) {
      return;
    }
    this._error = void 0;
    if (mode === "vacation") {
      this._openSheet();
      return;
    }
    if (mode === house.house_mode) {
      return;
    }
    const t5 = localize(this.hass, TEXTS2);
    setHouseMode(this.hass, mode).catch((error) => {
      this._error = t5.failed + errorMessage(error);
    });
  }
  _editSheet(change) {
    if (this._sheet) {
      this._sheet = { ...this._sheet, ...change, error: void 0 };
    }
  }
};
HouseModeSection.properties = {
  hass: { attribute: false },
  _house: { state: true },
  _sheet: { state: true },
  _error: { state: true }
};
HouseModeSection.styles = [
  sharedStyles,
  i`
      .seg {
        display: flex;
        border: 1px solid var(--cc-divider);
        border-radius: 10px;
        overflow: hidden;
      }
      .seg button {
        flex: 1;
        padding: 14px 6px;
        border: 0;
        background: transparent;
        color: var(--primary-text-color);
        font: inherit;
        font-weight: 500;
        cursor: pointer;
      }
      .seg button + button {
        border-left: 1px solid var(--cc-divider);
      }
      .seg button.on {
        background: var(--cc-primary);
        color: var(--text-primary-color, #fff);
      }
      .row-between {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
      }
      .btn {
        border: 1px solid var(--cc-divider);
        background: transparent;
        color: var(--primary-text-color);
        border-radius: 8px;
        padding: 8px 12px;
        min-height: 36px;
        font: inherit;
        cursor: pointer;
      }
      .btn.primary {
        background: var(--cc-primary);
        border-color: transparent;
        color: var(--text-primary-color, #fff);
      }
      .btn:disabled {
        opacity: 0.45;
        cursor: default;
      }
      .chip.static {
        cursor: default;
      }
      .chip.selected.warn {
        background: var(--cc-heat);
      }
      .err {
        color: var(--error-color, #d32f2f);
        font-size: 14px;
        margin: 10px 0 0;
      }
      ul.persons {
        list-style: none;
        margin: 0;
        padding: 0;
      }
      ul.persons li {
        display: flex;
        justify-content: space-between;
        gap: 8px;
        padding: 8px 0;
        border-top: 1px solid var(--cc-divider);
      }
      .presence-not_home {
        color: var(--cc-night);
      }
      .presence-unknown {
        color: var(--cc-muted);
      }
      .sheet-root {
        position: fixed;
        inset: 0;
        z-index: 50;
      }
      .backdrop {
        position: absolute;
        inset: 0;
        background: rgba(0, 0, 0, 0.45);
      }
      .sheet {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        max-height: 88vh;
        overflow: auto;
        background: var(--cc-card);
        color: var(--primary-text-color);
        border-radius: 16px 16px 0 0;
        padding: 18px 16px calc(18px + env(safe-area-inset-bottom));
      }
      .sheet h3 {
        margin: 0 0 4px;
        font-size: 18px;
        font-weight: 500;
      }
      .field-row {
        display: flex;
        gap: 12px;
      }
      .field-row label {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 4px;
        font-size: 13px;
        color: var(--cc-muted);
        margin: 10px 0;
      }
      .field-row input {
        font: inherit;
        font-size: 16px;
        color: var(--primary-text-color);
        background: var(--primary-background-color, #fafafa);
        border: 1px solid var(--cc-divider);
        border-radius: 8px;
        padding: 9px 10px;
        min-width: 0;
      }
      .sheet-actions {
        display: flex;
        gap: 8px;
        align-items: center;
        margin-top: 16px;
      }
      .spacer {
        flex: 1;
      }
      @media (min-width: 700px) {
        .sheet {
          left: 50%;
          right: auto;
          bottom: auto;
          top: 50%;
          transform: translate(-50%, -50%);
          width: 460px;
          border-radius: 16px;
        }
      }
    `
];
defineOnce("cc-house-mode-section", HouseModeSection);

// src/house/house-tab.ts
var HouseTab = class extends i4 {
  render() {
    return b2`
      <cc-house-mode-section .hass=${this.hass}></cc-house-mode-section>
      <cc-global-temperatures-section .hass=${this.hass}></cc-global-temperatures-section>
    `;
  }
};
HouseTab.properties = {
  hass: { attribute: false }
};
defineOnce("cc-house-tab", HouseTab);

// src/navigation.ts
var NAVIGATE_EVENT = "cc-navigate";
function navigate(from, tab, roomId) {
  from.dispatchEvent(
    new CustomEvent(NAVIGATE_EVENT, {
      detail: { tab, roomId },
      bubbles: true,
      composed: true
    })
  );
}

// src/house/house-status.ts
var TEXTS3 = {
  de: {
    auto: "Haus: Automatik",
    vacation: "Haus: Urlaub bis {end}",
    off: "Haus: Aus",
    away: "Abwesend",
    someoneHome: "Jemand zu Hause"
  },
  en: {
    auto: "House: automatic",
    vacation: "House: vacation until {end}",
    off: "House: off",
    away: "Away",
    someoneHome: "Someone at home"
  }
};
var HouseStatus = class extends i4 {
  constructor() {
    super(...arguments);
    this._openHouse = () => navigate(this, "house");
  }
  connectedCallback() {
    super.connectedCallback();
    this._subscribe();
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    this._unsubscribe?.then((unsubscribe) => unsubscribe()).catch(() => void 0);
    this._unsubscribe = void 0;
  }
  updated(changed) {
    if (changed.has("hass")) {
      this._subscribe();
    }
  }
  _subscribe() {
    if (!this.hass || !this.isConnected || this._unsubscribe) {
      return;
    }
    this._unsubscribe = subscribeHouse(this.hass, (house) => this._house = house);
    this._unsubscribe.catch(() => this._unsubscribe = void 0);
  }
  render() {
    const house = this._house;
    if (!house) {
      return A;
    }
    const t5 = localize(this.hass, TEXTS3);
    const mode = house.house_mode === "vacation" && house.vacation_end ? format(t5.vacation, { end: formatVacationEnd(language(this.hass), house.vacation_end) }) : house.house_mode === "off" ? t5.off : t5.auto;
    return b2`<div class="chips">
      <button
        class="chip ${house.house_mode === "auto" ? "" : "selected warn"}"
        @click=${this._openHouse}
      >
        ${mode}
      </button>
      <button class="chip ${house.away ? "selected warn" : ""}" @click=${this._openHouse}>
        ${house.away ? t5.away : t5.someoneHome}
      </button>
    </div>`;
  }
};
HouseStatus.properties = {
  hass: { attribute: false },
  _house: { state: true }
};
HouseStatus.styles = [
  sharedStyles,
  i`
      .chip.selected.warn {
        background: var(--cc-heat);
      }
    `
];
defineOnce("cc-house-status", HouseStatus);

// src/overview/overview-tab.ts
var UNDO_SECONDS = 6;
var TEXTS4 = {
  de: {
    auto: "Auto",
    heat: "Heizen",
    off: "Aus",
    target: "Soll",
    endOverride: "Antippen beendet die Übersteuerung → Auto",
    endOff: "Antippen beendet „Aus“ → Auto",
    pending: "Kehrt zu Auto zurück …",
    returning: "{room} kehrt zu Auto zurück",
    undo: "Rückgängig",
    dismiss: "OK",
    failed: "{room} konnte nicht auf Auto gestellt werden: {error}",
    noRooms: "Noch keine Räume. Lege sie in den Einstellungen der Integration an."
  },
  en: {
    auto: "Auto",
    heat: "Heat",
    off: "Off",
    target: "Target",
    endOverride: "Tap to end the override → Auto",
    endOff: "Tap to end “Off” → Auto",
    pending: "Returning to auto …",
    returning: "{room} returns to auto",
    undo: "Undo",
    dismiss: "OK",
    failed: "{room} could not be set to auto: {error}",
    noRooms: "No rooms yet. Add them in the settings of the integration."
  }
};
var REASON_COLOURS = {
  override: "heat",
  window_open: "frost",
  room_off: "off",
  house_off: "off",
  vacation: "night",
  away: "night"
};
var OverviewTab = class extends i4 {
  constructor() {
    super(...arguments);
    this.rooms = [];
    this._undo = () => {
      if (this._pending) {
        window.clearTimeout(this._pending.timer);
        this._pending = void 0;
      }
    };
    this._sendWhenHidden = () => {
      if (document.visibilityState === "hidden") {
        this._sendPending();
      }
    };
    this._sendPending = () => {
      const pending = this._pending;
      if (!pending || !this.hass) {
        return;
      }
      window.clearTimeout(pending.timer);
      this._pending = void 0;
      returnToAuto(this.hass, pending.roomId).catch((error) => {
        const t5 = localize(this.hass, TEXTS4);
        this._error = format(t5.failed, { room: pending.name, error: errorMessage(error) });
      });
    };
  }
  connectedCallback() {
    super.connectedCallback();
    document.addEventListener("visibilitychange", this._sendWhenHidden);
    window.addEventListener("pagehide", this._sendPending);
  }
  disconnectedCallback() {
    document.removeEventListener("visibilitychange", this._sendWhenHidden);
    window.removeEventListener("pagehide", this._sendPending);
    this._sendPending();
    super.disconnectedCallback();
  }
  render() {
    const t5 = localize(this.hass, TEXTS4);
    return b2`
      <cc-house-status .hass=${this.hass}></cc-house-status>
      ${this.rooms.length === 0 ? b2`<p class="muted">${t5.noRooms}</p>` : A}
      <div class="grid">${this.rooms.map((room2) => this._card(room2, t5))}</div>
      ${this._toast(t5)}
    `;
  }
  _card(room2, t5) {
    const pending = this._pending?.roomId === room2.room_id;
    const mode = pending ? "auto" : room2.room_mode;
    const colour = REASON_COLOURS[room2.reason_code ?? ""] ?? "auto";
    let foot = A;
    if (pending) {
      foot = t5.pending;
    } else if (room2.room_mode === "heat") {
      foot = t5.endOverride;
    } else if (room2.room_mode === "off") {
      foot = t5.endOff;
    }
    return b2`
      <div
        class="card room colour-${colour} ${pending ? "pending" : ""}"
        role="button"
        tabindex="0"
        @click=${() => this._tap(room2)}
        @keydown=${(event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        this._tap(room2);
      }
    }}
      >
        <div class="top">
          <span class="name">${room2.name}</span>
          <span class="mode mode-${mode}">${t5[mode]}</span>
        </div>
        <div class="temps">
          <span class="current">${formatTemperature(this.hass, room2.current_temperature)}</span>
          <span class="target">
            <span class="muted">${t5.target}</span>
            ${formatTemperature(this.hass, room2.target_temperature)}
          </span>
        </div>
        <div class="reason">${room2.reason ?? ""}</div>
        <div class="foot ${pending ? "muted" : ""}">${foot}</div>
      </div>
    `;
  }
  _toast(t5) {
    if (this._pending) {
      return b2`<div class="toast" role="status">
        <span>${format(t5.returning, { room: this._pending.name })}</span>
        <button @click=${this._undo}>${t5.undo}</button>
      </div>`;
    }
    if (this._error) {
      return b2`<div class="toast" role="alert">
        <span>${this._error}</span>
        <button @click=${() => this._error = void 0}>${t5.dismiss}</button>
      </div>`;
    }
    return A;
  }
  _tap(room2) {
    if (this._pending?.roomId === room2.room_id) {
      return;
    }
    if (room2.room_mode === "auto") {
      navigate(this, "rooms", room2.room_id);
      return;
    }
    this._sendPending();
    this._error = void 0;
    this._pending = {
      roomId: room2.room_id,
      name: room2.name,
      timer: window.setTimeout(this._sendPending, UNDO_SECONDS * 1e3)
    };
  }
};
OverviewTab.properties = {
  hass: { attribute: false },
  rooms: { attribute: false },
  _pending: { state: true },
  _error: { state: true }
};
OverviewTab.styles = [
  sharedStyles,
  i`
      .grid {
        display: grid;
        gap: 12px;
        grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
      }
      .grid > .card {
        margin: 0;
      }
      .room {
        padding: 14px;
        border-left: 5px solid var(--cc-auto);
        cursor: pointer;
        user-select: none;
        -webkit-user-select: none;
      }
      .room:active {
        filter: brightness(0.96);
      }
      .room:focus-visible {
        outline: 2px solid var(--cc-primary);
      }
      .colour-heat {
        border-left-color: var(--cc-heat);
      }
      .colour-frost {
        border-left-color: var(--cc-frost);
      }
      .colour-off {
        border-left-color: var(--cc-off);
      }
      .colour-night {
        border-left-color: var(--cc-night);
      }
      .pending {
        opacity: 0.7;
      }
      .top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
      }
      .name {
        font-size: 17px;
        font-weight: 500;
      }
      .mode {
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 13px;
        font-weight: 500;
        color: #fff;
      }
      .mode-auto {
        background: var(--cc-auto);
      }
      .mode-heat {
        background: var(--cc-heat);
      }
      .mode-off {
        background: var(--cc-off);
      }
      .temps {
        display: flex;
        align-items: baseline;
        gap: 14px;
        margin: 6px 0 2px;
      }
      .current {
        font-size: 30px;
      }
      .target {
        font-size: 16px;
      }
      .reason {
        font-size: 15px;
      }
      .foot {
        margin-top: 8px;
        min-height: 20px;
        font-size: 13px;
        font-weight: 500;
        color: var(--cc-heat);
      }
      .foot.muted {
        color: var(--cc-muted);
        font-weight: normal;
      }
      .toast {
        position: fixed;
        left: 50%;
        transform: translateX(-50%);
        bottom: calc(16px + env(safe-area-inset-bottom));
        z-index: 10;
        display: flex;
        gap: 14px;
        align-items: center;
        width: max-content;
        max-width: calc(100vw - 32px);
        padding: 10px 14px;
        background: #323232;
        color: #fff;
        border-radius: 8px;
        font-size: 14px;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
      }
      .toast button {
        border: 0;
        background: transparent;
        color: #81d4fa;
        font: inherit;
        font-weight: 600;
        padding: 6px 4px;
        cursor: pointer;
      }
    `
];
defineOnce("cc-overview-tab", OverviewTab);

// src/rooms/levels-section.ts
var TEXTS5 = {
  de: {
    title: "Stufen und Vorlaufzeit",
    comfort: "Komfort",
    night: "Nacht",
    eco: "Eco",
    leadTime: "Vorlaufzeit",
    leadTimeNote: "So lange vor Beginn eines Blocks gilt bereits seine Stufe, wenn sie wärmer ist.",
    warmer: "{level} ist wärmer als Komfort – gewollt?",
    less: "{name} weniger",
    more: "{name} mehr",
    loading: "Lade Stufen …",
    failed: "Konnte nicht gespeichert werden: {error}",
    loadFailed: "Stufen konnten nicht geladen werden: {error}"
  },
  en: {
    title: "Levels and lead time",
    comfort: "Comfort",
    night: "Night",
    eco: "Eco",
    leadTime: "Lead time",
    leadTimeNote: "A warmer level of a block already applies this long before the block starts.",
    warmer: "{level} is warmer than comfort – intended?",
    less: "{name} lower",
    more: "{name} higher",
    loading: "Loading levels …",
    failed: "Could not be saved: {error}",
    loadFailed: "Levels could not be loaded: {error}"
  }
};
var LEVELS = ["comfort", "night", "eco"];
function formatLeadTime(minutes2) {
  const total = Math.round(minutes2);
  const hours = Math.floor(total / 60);
  const rest = total % 60;
  if (hours === 0) {
    return `${rest} min`;
  }
  return rest === 0 ? `${hours} h` : `${hours} h ${rest} min`;
}
var RoomLevelsSection = class extends i4 {
  connectedCallback() {
    super.connectedCallback();
    this._save?.connect();
  }
  disconnectedCallback() {
    this._save?.disconnect();
    super.disconnectedCallback();
  }
  willUpdate(changed) {
    if ((changed.has("room") || changed.has("hass")) && this.room?.room_id !== this._loadedRoomId) {
      this._load();
    }
  }
  _load() {
    const hass = this.hass;
    const roomId = this.room?.room_id;
    if (!hass || !roomId) {
      return;
    }
    this._save?.disconnect();
    this._loadedRoomId = roomId;
    this._levels = void 0;
    this._error = void 0;
    this._save = new DelayedSave((changes) => this._send(hass, roomId, changes));
    this._save.connect();
    getRoomLevels(hass, roomId).then((levels) => {
      if (this._loadedRoomId === roomId) {
        this._levels = levels;
      }
    }).catch((error) => {
      if (this._loadedRoomId === roomId) {
        this._error = format(localize(this.hass, TEXTS5).loadFailed, { error: errorMessage(error) });
      }
    });
  }
  _send(hass, roomId, changes) {
    if (this._loadedRoomId === roomId && this._levels) {
      this._levels = { ...this._levels, ...changes };
    }
    setRoomLevels(hass, roomId, changes).catch((error) => {
      if (this._loadedRoomId === roomId) {
        this._loadedRoomId = void 0;
        this._load();
        this._error = format(localize(this.hass, TEXTS5).failed, { error: errorMessage(error) });
      }
    });
  }
  render() {
    const t5 = localize(this.hass, TEXTS5);
    return b2`<h2 class="section">${t5.title}</h2>
      <div class="card pad">${this._body(t5)}</div>`;
  }
  _body(t5) {
    if (!this._levels) {
      return this._error ? b2`<p class="error" role="alert">${this._error}</p>` : b2`<span class="muted small">${t5.loading}</span>`;
    }
    const levels = { ...this._levels, ...this._save?.changes };
    const warmer = ["night", "eco"].filter(
      (level) => levels[`${level}_temperature`] > levels.comfort_temperature
    );
    return b2`
      ${LEVELS.map((level) => this._temperatureRow(t5, levels, level))}
      ${warmer.map(
      (level) => b2`<p class="hint small" role="status">${format(t5.warmer, { level: t5[level] })}</p>`
    )}
      ${stepper({
      label: t5.leadTime,
      value: formatLeadTime(levels.lead_time_minutes),
      less: format(t5.less, { name: t5.leadTime }),
      more: format(t5.more, { name: t5.leadTime }),
      canDown: levels.lead_time_minutes > 0,
      canUp: levels.lead_time_minutes < MAX_LEAD_TIME_MINUTES,
      onStep: (direction) => this._change({ lead_time_minutes: stepLeadTime(levels.lead_time_minutes, direction) })
    })}
      <p class="muted small note">${t5.leadTimeNote}</p>
      ${this._error ? b2`<p class="error small" role="alert">${this._error}</p>` : A}
    `;
  }
  _temperatureRow(t5, levels, level) {
    const key = `${level}_temperature`;
    const value = levels[key];
    return stepper({
      label: b2`<i class="dot dot-${level}"></i>${t5[level]}`,
      value: formatTemperature(this.hass, value),
      less: format(t5.less, { name: t5[level] }),
      more: format(t5.more, { name: t5[level] }),
      canDown: value > MIN_TEMPERATURE,
      canUp: value < MAX_TEMPERATURE,
      onStep: (direction) => this._change({ [key]: stepTemperature(value, direction) })
    });
  }
  _change(changes) {
    this._error = void 0;
    this._save?.change(changes);
    this.requestUpdate();
  }
};
RoomLevelsSection.properties = {
  hass: { attribute: false },
  room: { attribute: false },
  _levels: { state: true },
  _error: { state: true }
};
RoomLevelsSection.styles = [
  sharedStyles,
  stepperStyles,
  i`
      .dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
      }
      .dot-comfort {
        background: #ffb300;
      }
      .dot-night {
        background: var(--cc-night);
      }
      .dot-eco {
        background: #8bc34a;
      }
      .note {
        margin: 4px 0 0;
      }
    `
];
defineOnce("cc-room-levels-section", RoomLevelsSection);

// node_modules/lit-html/directive.js
var t3 = { ATTRIBUTE: 1, CHILD: 2, PROPERTY: 3, BOOLEAN_ATTRIBUTE: 4, EVENT: 5, ELEMENT: 6 };
var e4 = (t5) => (...e5) => ({ _$litDirective$: t5, values: e5 });
var i5 = class {
  constructor(t5) {
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AT(t5, e5, i6) {
    this._$Ct = t5, this._$AM = e5, this._$Ci = i6;
  }
  _$AS(t5, e5) {
    return this.update(t5, e5);
  }
  update(t5, e5) {
    return this.render(...e5);
  }
};

// node_modules/lit-html/directive-helpers.js
var { I: t4 } = j;
var r4 = (o5) => void 0 === o5.strings;
var m2 = {};
var p3 = (o5, t5 = m2) => o5._$AH = t5;

// node_modules/lit-html/directives/live.js
var l3 = e4(class extends i5 {
  constructor(r5) {
    if (super(r5), r5.type !== t3.PROPERTY && r5.type !== t3.ATTRIBUTE && r5.type !== t3.BOOLEAN_ATTRIBUTE) throw Error("The `live` directive is not allowed on child or event bindings");
    if (!r4(r5)) throw Error("`live` bindings can only contain a single expression");
  }
  render(r5) {
    return r5;
  }
  update(i6, [t5]) {
    if (t5 === E || t5 === A) return t5;
    const o5 = i6.element, l4 = i6.name;
    if (i6.type === t3.PROPERTY) {
      if (t5 === o5[l4]) return E;
    } else if (i6.type === t3.BOOLEAN_ATTRIBUTE) {
      if (!!t5 === o5.hasAttribute(l4)) return E;
    } else if (i6.type === t3.ATTRIBUTE && o5.getAttribute(l4) === t5 + "") return E;
    return p3(i6), t5;
  }
});

// src/api/schedules.ts
var WEEKDAYS = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday"
];
function subscribeAssignments(hass, onAssignments) {
  return hass.connection.subscribeMessage(onAssignments, {
    type: "hyggely/schedules/subscribe"
  });
}
function assignSchedule(hass, roomId, schedule) {
  return hass.callWS({
    type: "hyggely/room/assign_schedule",
    room_id: roomId,
    ..."scheduleId" in schedule ? { schedule_id: schedule.scheduleId } : { entity_id: schedule.entityId }
  });
}
function listSchedules(hass) {
  return hass.callWS({ type: "schedule/list" });
}
function createSchedule(hass, name, week) {
  return hass.callWS({ type: "schedule/create", name, ...week });
}
function updateSchedule(hass, item) {
  const { id, ...fields } = item;
  return hass.callWS({ type: "schedule/update", schedule_id: id, ...fields });
}
function deleteSchedule(hass, scheduleId) {
  return hass.callWS({ type: "schedule/delete", schedule_id: scheduleId });
}

// src/rooms/schedule-week.ts
var DAY = 24 * 60;
var STEP = 15;
var NEW_BLOCK_MINUTES = 60;
var WORKDAYS = [0, 1, 2, 3, 4];
var WEEKEND = [5, 6];
var ALL_DAYS = [0, 1, 2, 3, 4, 5, 6];
function minutes(time) {
  const [hours, mins] = time.split(":").map(Number);
  return hours * 60 + mins;
}
function pad2(value) {
  return String(value).padStart(2, "0");
}
function clock(value) {
  return `${pad2(Math.floor(value / 60))}:${pad2(value % 60)}`;
}
function levelOf(data) {
  return data?.level === "night" ? "night" : "comfort";
}
function weekOf(item) {
  return WEEKDAYS.map(
    (weekday) => sorted(
      (item[weekday] ?? []).map((block2) => ({
        from: minutes(block2.from),
        to: minutes(block2.to),
        level: levelOf(block2.data),
        data: block2.data ?? {}
      }))
    )
  );
}
function scheduleWeekOf(week) {
  const result = {};
  WEEKDAYS.forEach((weekday, day) => {
    result[weekday] = week[day].map(
      (block2) => ({
        from: `${clock(block2.from)}:00`,
        to: `${clock(block2.to)}:00`,
        data: { ...block2.data, level: block2.level }
      })
    );
  });
  return result;
}
function sorted(blocks) {
  return [...blocks].sort((a3, b3) => a3.from - b3.from);
}
function block(from, to, level = "comfort") {
  return { from, to, level, data: {} };
}
function emptyWeek() {
  return ALL_DAYS.map(() => []);
}
function standardWeek() {
  const workday = [block(0, 6 * 60, "night"), block(6 * 60, 8 * 60), block(16 * 60, 21 * 60), block(21 * 60, DAY, "night")];
  const weekend = [block(0, 7 * 60 + 30, "night"), block(7 * 60 + 30, 21 * 60), block(21 * 60, DAY, "night")];
  return ALL_DAYS.map((day) => (WEEKEND.includes(day) ? weekend : workday).map((b3) => ({ ...b3, data: {} })));
}
function copyWeek(week) {
  return week.map((blocks) => blocks.map((b3) => ({ ...b3, data: { ...b3.data } })));
}
function overlaps(blocks, from, to, ignore = -1) {
  return blocks.some((b3, index) => index !== ignore && from < b3.to && to > b3.from);
}
function room(blocks, index) {
  return {
    lo: index > 0 ? blocks[index - 1].to : 0,
    hi: index < blocks.length - 1 ? blocks[index + 1].from : DAY
  };
}
function freeRange(blocks, preferred, length) {
  for (const candidate of [preferred, ...blocks.map((b3) => b3.to), 0]) {
    const from = Math.max(0, Math.min(DAY - STEP, candidate));
    if (blocks.some((b3) => from >= b3.from && from < b3.to)) {
      continue;
    }
    const next = Math.min(DAY, ...blocks.filter((b3) => b3.from > from).map((b3) => b3.from));
    if (next - from >= STEP) {
      return { from, to: Math.min(from + length, next) };
    }
  }
  return null;
}
function withDay(week, day, blocks) {
  return week.map((current, index) => index === day ? sorted(blocks) : current);
}
function copyBlock(week, day, index, targets) {
  const source = week[day][index];
  const skipped = [];
  let result = week;
  for (const target of targets) {
    if (target === day) {
      continue;
    }
    if (overlaps(result[target], source.from, source.to)) {
      skipped.push(target);
      continue;
    }
    result = withDay(result, target, [...result[target], { ...source, data: { ...source.data } }]);
  }
  return { week: result, skipped };
}
function copyDay(week, day, targets) {
  return week.map(
    (blocks, index) => targets.includes(index) && index !== day ? week[day].map((b3) => ({ ...b3, data: { ...b3.data } })) : blocks
  );
}
function acrossMidnight(week, day, index) {
  const current = week[day][index];
  const result = {};
  if (current.to === DAY) {
    const next = (day + 1) % 7;
    const counterpart = week[next].find((b3) => b3.from === 0);
    if (counterpart) {
      result.continuesUntil = { day: next, to: counterpart.to };
    }
  }
  if (current.from === 0) {
    const previous = (day + 6) % 7;
    const counterpart = week[previous].find((b3) => b3.to === DAY);
    if (counterpart) {
      result.since = { day: previous, from: counterpart.from };
    }
  }
  return result;
}
function today() {
  return ((/* @__PURE__ */ new Date()).getDay() + 6) % 7;
}
function nowMinutes() {
  const now = /* @__PURE__ */ new Date();
  return now.getHours() * 60 + now.getMinutes();
}

// src/rooms/create-schedule-sheet.ts
var TEXTS6 = {
  de: {
    title: "Neuer Zeitplan für {room}",
    name: "Name",
    defaultName: "Heizung {room}",
    nameTaken: "Diesen Namen hat schon ein Zeitplan.",
    nameMissing: "Bitte einen Namen eingeben.",
    template: "Vorlage",
    standard: "Standardwoche",
    standardHint: "Mo–Fr Komfort 6–8 und 16–21 Uhr, Sa–So 7:30–21 Uhr, nachts Nacht",
    empty: "Leer",
    emptyHint: "Ganztägig Eco, Blöcke legst du danach an",
    copyOf: "Kopie von „{name}“",
    copyHint: "Gleiche Blöcke, danach unabhängig änderbar",
    assigns: "Der neue Zeitplan gilt danach für {room}.",
    cancel: "Abbrechen",
    create: "Anlegen und zuweisen"
  },
  en: {
    title: "New schedule for {room}",
    name: "Name",
    defaultName: "Heating {room}",
    nameTaken: "A schedule with this name exists already.",
    nameMissing: "Please enter a name.",
    template: "Template",
    standard: "Standard week",
    standardHint: "Mon–Fri comfort 6–8 and 16–21, Sat–Sun 7:30–21, night at night",
    empty: "Empty",
    emptyHint: "Eco all day, add blocks afterwards",
    copyOf: "Copy of “{name}”",
    copyHint: "Same blocks, changeable on its own afterwards",
    assigns: "The new schedule then applies to {room}.",
    cancel: "Cancel",
    create: "Create and assign"
  }
};
var CreateScheduleSheet = class extends i4 {
  constructor() {
    super(...arguments);
    this.roomName = "";
    this.takenNames = [];
    this.sources = [];
    this.busy = false;
    /** `standard`, `empty` or the id of a copy source. */
    this._template = "standard";
    this._cancel = () => {
      this.dispatchEvent(new CustomEvent("cc-cancel"));
    };
    this._create = () => {
      const name = (this._name ?? "").trim();
      if (!name || this._taken(name)) {
        return;
      }
      this.dispatchEvent(new CustomEvent("cc-create", { detail: { name, week: this._week() } }));
    };
  }
  willUpdate(changed) {
    if (this._name === void 0) {
      this._name = this._suggestedName();
    }
    if (changed.has("preselect") && this.preselect) {
      this._template = this.preselect;
    }
  }
  _suggestedName() {
    const base = format(localize(this.hass, TEXTS6).defaultName, { room: this.roomName });
    let name = base;
    for (let index = 2; this._taken(name); index++) {
      name = `${base} ${index}`;
    }
    return name;
  }
  _taken(name) {
    const wanted = name.trim().toLocaleLowerCase();
    return this.takenNames.some((taken) => taken.trim().toLocaleLowerCase() === wanted);
  }
  render() {
    const t5 = localize(this.hass, TEXTS6);
    const name = this._name ?? "";
    const problem = !name.trim() ? t5.nameMissing : this._taken(name) ? t5.nameTaken : void 0;
    const options = [
      { id: "standard", label: t5.standard, hint: t5.standardHint },
      { id: "empty", label: t5.empty, hint: t5.emptyHint },
      ...this.sources.map((source) => ({ id: source.id, label: format(t5.copyOf, { name: source.name }), hint: t5.copyHint }))
    ];
    return b2`<div class="sheet-root">
      <div class="backdrop" @click=${this._cancel}></div>
      <div class="sheet" role="dialog" aria-modal="true" aria-labelledby="create-title">
        <h3 id="create-title">${format(t5.title, { room: this.roomName })}</h3>
        <label class="field"
          >${t5.name}
          <input .value=${name} @input=${(event) => this._name = event.target.value}
        /></label>
        ${problem ? b2`<p class="err small">${problem}</p>` : A}
        <div class="field">${t5.template}</div>
        <div class="options" role="radiogroup">
          ${options.map(
      (option) => b2`<label class="option ${this._template === option.id ? "on" : ""}">
              <input
                type="radio"
                name="template"
                .checked=${this._template === option.id}
                @change=${() => this._template = option.id}
              />
              <span><b>${option.label}</b><br /><span class="muted small">${option.hint}</span></span>
            </label>`
    )}
        </div>
        <p class="muted small">${format(t5.assigns, { room: this.roomName })}</p>
        ${this.error ? b2`<p class="err" role="alert">${this.error}</p>` : A}
        <div class="sheet-actions">
          <span class="spacer"></span>
          <button class="btn" @click=${this._cancel}>${t5.cancel}</button>
          <button class="btn primary" ?disabled=${this.busy || problem !== void 0} @click=${this._create}>
            ${t5.create}
          </button>
        </div>
      </div>
    </div>`;
  }
  _week() {
    if (this._template === "standard") {
      return standardWeek();
    }
    const source = this.sources.find((candidate) => candidate.id === this._template);
    return source ? copyWeek(source.week) : emptyWeek();
  }
};
CreateScheduleSheet.properties = {
  hass: { attribute: false },
  roomName: { attribute: false },
  takenNames: { attribute: false },
  sources: { attribute: false },
  preselect: { attribute: false },
  busy: { attribute: false },
  error: { attribute: false },
  _name: { state: true },
  _template: { state: true }
};
CreateScheduleSheet.styles = [
  sharedStyles,
  i`
      .sheet-root {
        position: fixed;
        inset: 0;
        z-index: 50;
      }
      .backdrop {
        position: absolute;
        inset: 0;
        background: rgba(0, 0, 0, 0.45);
      }
      .sheet {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        max-height: 88vh;
        overflow: auto;
        background: var(--cc-card);
        color: var(--primary-text-color);
        border-radius: 16px 16px 0 0;
        padding: 18px 16px calc(18px + env(safe-area-inset-bottom));
      }
      .sheet h3 {
        margin: 0 0 8px;
        font-size: 18px;
        font-weight: 500;
      }
      .field {
        display: flex;
        flex-direction: column;
        gap: 4px;
        font-size: 13px;
        color: var(--cc-muted);
        margin: 10px 0 6px;
      }
      .field input {
        font: inherit;
        font-size: 16px;
        color: var(--primary-text-color);
        background: var(--primary-background-color, #fafafa);
        border: 1px solid var(--cc-divider);
        border-radius: 8px;
        padding: 9px 10px;
      }
      .options {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .option {
        display: flex;
        gap: 10px;
        align-items: flex-start;
        border: 1px solid var(--cc-divider);
        border-radius: 10px;
        padding: 10px;
        cursor: pointer;
      }
      .option.on {
        border-color: var(--cc-primary);
        box-shadow: 0 0 0 1px var(--cc-primary);
      }
      .err {
        color: var(--error-color, #d32f2f);
        font-size: 14px;
        margin: 6px 0 0;
      }
      .sheet-actions {
        display: flex;
        gap: 8px;
        align-items: center;
        margin-top: 16px;
      }
      .spacer {
        flex: 1;
      }
      .btn {
        border: 1px solid var(--cc-divider);
        background: transparent;
        color: var(--primary-text-color);
        border-radius: 8px;
        padding: 8px 12px;
        min-height: 36px;
        font: inherit;
        cursor: pointer;
      }
      .btn.primary {
        background: var(--cc-primary);
        border-color: transparent;
        color: var(--text-primary-color, #fff);
      }
      .btn:disabled {
        opacity: 0.45;
        cursor: default;
      }
      @media (min-width: 700px) {
        .sheet {
          left: 50%;
          right: auto;
          bottom: auto;
          top: 50%;
          transform: translate(-50%, -50%);
          width: 460px;
          border-radius: 16px;
        }
      }
    `
];
defineOnce("cc-create-schedule-sheet", CreateScheduleSheet);

// src/rooms/schedule-timeline.ts
var PX_PER_HOUR = 40;
var PX_PER_MINUTE = PX_PER_HOUR / 60;
var TEXTS7 = {
  de: {
    days: "Mo,Di,Mi,Do,Fr,Sa,So",
    longDays: "Montag,Dienstag,Mittwoch,Donnerstag,Freitag,Samstag,Sonntag",
    comfort: "Komfort",
    night: "Nacht",
    hintIdle: "Block antippen zum Auswählen · leere Stelle antippen für einen neuen Block",
    hintSelected: "Griff oben/unten ziehen ändert Beginn/Ende, den Block selbst ziehen verschiebt ihn (15-Minuten-Raster).",
    toComfort: "Auf Komfort stellen",
    toNight: "Auf Nacht stellen",
    copyBlock: "Kopieren nach …",
    remove: "Löschen",
    done: "Fertig",
    copyDay: "Tag kopieren nach …",
    copyBlockTitle: "{block} kopieren nach:",
    copyDayTitle: "{day} kopieren nach:",
    replaces: "Ersetzt die vorhandenen Blöcke an den gewählten Tagen.",
    workdays: "Mo–Fr",
    weekend: "Sa–So",
    all: "Alle",
    copy: "Kopieren ({count})",
    cancel: "Abbrechen",
    noRoom: "An diesem Tag ist kein Platz mehr frei.",
    continues: "geht weiter bis {day} {time}",
    since: "seit {day} {time}",
    noBlocks: "Keine Blöcke – ganztägig Eco"
  },
  en: {
    days: "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
    longDays: "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday",
    comfort: "Comfort",
    night: "Night",
    hintIdle: "Tap a block to select it · tap an empty spot for a new block",
    hintSelected: "Drag the top/bottom handle to change start/end, drag the block itself to move it (15-minute steps).",
    toComfort: "Set to comfort",
    toNight: "Set to night",
    copyBlock: "Copy to …",
    remove: "Delete",
    done: "Done",
    copyDay: "Copy day to …",
    copyBlockTitle: "Copy {block} to:",
    copyDayTitle: "Copy {day} to:",
    replaces: "Replaces the blocks on the chosen days.",
    workdays: "Mon–Fri",
    weekend: "Sat–Sun",
    all: "All",
    copy: "Copy ({count})",
    cancel: "Cancel",
    noRoom: "There is no free time left on this day.",
    continues: "continues until {day} {time}",
    since: "since {day} {time}",
    noBlocks: "No blocks – eco all day"
  }
};
var ScheduleTimeline = class extends i4 {
  constructor() {
    super(...arguments);
    this.week = [];
    this.day = today();
    this._suppressClick = false;
    this._tapLane = (event) => {
      if (this._suppressClick || event.target !== event.currentTarget) {
        return;
      }
      if (this._selected !== void 0) {
        this._selected = void 0;
        this._copy = void 0;
        return;
      }
      const t5 = localize(this.hass, TEXTS7);
      const lane = event.currentTarget;
      const minute = Math.floor((event.clientY - lane.getBoundingClientRect().top) / PX_PER_MINUTE / STEP) * STEP;
      const blocks = this.week[this.day];
      const range = freeRange(blocks, minute, NEW_BLOCK_MINUTES);
      if (!range) {
        this._note = t5.noRoom;
        return;
      }
      const added = { ...range, level: "comfort", data: {} };
      const week = withDay(this.week, this.day, [...blocks, added]);
      this._selected = week[this.day].findIndex((b3) => b3.from === added.from);
      this._note = void 0;
      this._emit({ week, label: this._describe(this.day, added, t5) });
    };
    this._toggleLevel = () => {
      const index = this._selected;
      if (index === void 0) {
        return;
      }
      const t5 = localize(this.hass, TEXTS7);
      const blocks = [...this.week[this.day]];
      const level = blocks[index].level === "comfort" ? "night" : "comfort";
      blocks[index] = { ...blocks[index], level };
      this._emit({ week: withDay(this.week, this.day, blocks), label: this._describe(this.day, blocks[index], t5) });
    };
    this._remove = () => {
      const index = this._selected;
      if (index === void 0) {
        return;
      }
      const t5 = localize(this.hass, TEXTS7);
      const removed = this.week[this.day][index];
      this._selected = void 0;
      this._copy = void 0;
      this._emit({
        week: withDay(
          this.week,
          this.day,
          this.week[this.day].filter((_2, i6) => i6 !== index)
        ),
        label: `${this._describe(this.day, removed, t5)} ✕`
      });
    };
    this._done = () => {
      this._selected = void 0;
      this._copy = void 0;
    };
    this._doCopy = () => {
      const copy = this._copy;
      if (!copy || copy.targets.length === 0) {
        return;
      }
      const t5 = localize(this.hass, TEXTS7);
      const days = t5.days.split(",");
      const targets = copy.targets.map((d3) => days[d3]).join(", ");
      this._copy = void 0;
      if (copy.kind === "day") {
        this._emit({
          week: copyDay(this.week, this.day, copy.targets),
          label: `${format(t5.copyDayTitle, { day: t5.longDays.split(",")[this.day] })} ${targets}`
        });
        return;
      }
      const index = this._selected;
      if (index === void 0) {
        return;
      }
      const result = copyBlock(this.week, this.day, index, copy.targets);
      this._emit({
        week: result.week,
        label: `${format(t5.copyBlockTitle, { block: this._describe(this.day, this.week[this.day][index], t5) })} ${targets}`,
        skipped: result.skipped
      });
    };
    this._moveDrag = (event) => {
      const drag = this._drag;
      if (!drag || event.pointerId !== drag.pointerId) {
        return;
      }
      const delta = Math.round((event.clientY - drag.startY) / PX_PER_MINUTE / STEP) * STEP;
      let { from, to } = drag.original;
      if (drag.mode === "move") {
        const length = to - from;
        from = Math.min(Math.max(from + delta, drag.lo), drag.hi - length);
        to = from + length;
      } else if (drag.mode === "top") {
        from = Math.min(Math.max(from + delta, drag.lo), to - STEP);
      } else {
        to = Math.max(Math.min(to + delta, drag.hi), from + STEP);
      }
      if (from !== drag.from || to !== drag.to) {
        this._drag = { ...drag, from, to };
      }
    };
    this._endDrag = (event) => {
      const drag = this._drag;
      const index = this._selected;
      if (!drag || event.pointerId !== drag.pointerId || index === void 0) {
        return;
      }
      this._drag = void 0;
      if (drag.from === drag.original.from && drag.to === drag.original.to) {
        return;
      }
      this._suppressClick = true;
      window.setTimeout(() => this._suppressClick = false, 50);
      const t5 = localize(this.hass, TEXTS7);
      const blocks = [...this.week[this.day]];
      blocks[index] = { ...drag.original, from: drag.from, to: drag.to };
      this._emit({ week: withDay(this.week, this.day, blocks), label: this._describe(this.day, blocks[index], t5) });
    };
    this._cancelDrag = () => {
      this._drag = void 0;
    };
  }
  willUpdate(changed) {
    if (changed.has("day")) {
      this._selected = void 0;
      this._copy = void 0;
      this._note = void 0;
    }
    if (this._selected !== void 0 && !this.week[this.day]?.[this._selected]) {
      this._selected = void 0;
    }
  }
  render() {
    const t5 = localize(this.hass, TEXTS7);
    if (this.week.length !== 7) {
      return A;
    }
    const days = t5.days.split(",");
    const selected = this._selected !== void 0 ? this.week[this.day][this._selected] : void 0;
    return b2`
      <div class="card week">
        ${days.map(
      (name, day) => b2`<button
            class="weekrow ${day === this.day ? "on" : ""}"
            aria-pressed=${day === this.day ? "true" : "false"}
            @click=${() => this._chooseDay(day)}
          >
            <span class="wd ${day === today() ? "today" : ""}">${name}</span>
            <span class="mini">
              ${this.week[day].map(
        (b3) => b2`<i
                    class="lvl-${b3.level}"
                    style="left:${b3.from / DAY * 100}%;width:${(b3.to - b3.from) / DAY * 100}%"
                  ></i>`
      )}
            </span>
          </button>`
    )}
      </div>
      <p class="hint muted small">${selected ? t5.hintSelected : t5.hintIdle}</p>
      ${selected ? this._toolbar(selected, t5) : A} ${this._copyPanel(t5)}
      ${this._note ? b2`<p class="note" role="status">${this._note}</p>` : A}
      <div class="card dayview">
        <div class="dayhead">
          <span>${t5.longDays.split(",")[this.day]}</span>
          <button class="btn small" @click=${() => this._openCopy("day")}>${t5.copyDay}</button>
        </div>
        ${this._edgeHint("top", t5)}
        <div class="timeline" style="height:${24 * PX_PER_HOUR}px">
          ${Array.from({ length: 25 }, (_2, hour) => b2`<div class="hour" style="top:${hour * PX_PER_HOUR}px"><span>${clock(hour * 60)}</span></div>`)}
          <div class="lane" @click=${this._tapLane}>
            ${this.week[this.day].map((b3, index) => this._block(b3, index, t5))}
            ${this.day === today() ? b2`<div class="now" style="top:${nowMinutes() * PX_PER_MINUTE}px"></div>` : A}
          </div>
        </div>
        ${this._edgeHint("bottom", t5)}
        ${this.week[this.day].length === 0 ? b2`<p class="muted small center">${t5.noBlocks}</p>` : A}
      </div>
    `;
  }
  _block(b3, index, t5) {
    const isSelected = index === this._selected;
    const drag = isSelected ? this._drag : void 0;
    const from = drag ? drag.from : b3.from;
    const to = drag ? drag.to : b3.to;
    return b2`<div
      class="block lvl-${b3.level} ${isSelected ? "selected" : ""}"
      style="top:${from * PX_PER_MINUTE}px;height:${(to - from) * PX_PER_MINUTE}px"
      @click=${(event) => this._tapBlock(event, index)}
      @pointerdown=${isSelected ? (event) => this._startDrag(event, "move") : A}
      @pointermove=${isSelected ? this._moveDrag : A}
      @pointerup=${isSelected ? this._endDrag : A}
      @pointercancel=${isSelected ? this._cancelDrag : A}
    >
      ${isSelected ? b2`<div class="handle top" @pointerdown=${(event) => this._startDrag(event, "top")}></div>
            <div class="handle bottom" @pointerdown=${(event) => this._startDrag(event, "bottom")}></div>` : A}
      <div class="label"><b>${clock(from)} – ${clock(to)}</b> ${t5[b3.level]}</div>
    </div>`;
  }
  _edgeHint(edge, t5) {
    const blocks = this.week[this.day];
    const index = edge === "top" ? blocks.findIndex((b3) => b3.from === 0) : blocks.findIndex((b3) => b3.to === DAY);
    if (index < 0) {
      return A;
    }
    const days = t5.days.split(",");
    const counterpart = acrossMidnight(this.week, this.day, index);
    if (edge === "top" && counterpart.since) {
      return b2`<p class="edge muted small">↑ ${format(t5.since, { day: days[counterpart.since.day], time: clock(counterpart.since.from) })}</p>`;
    }
    if (edge === "bottom" && counterpart.continuesUntil) {
      return b2`<p class="edge muted small">
        ↓ ${format(t5.continues, { day: days[counterpart.continuesUntil.day], time: clock(counterpart.continuesUntil.to) })}
      </p>`;
    }
    return A;
  }
  _toolbar(selected, t5) {
    return b2`<div class="card toolbar">
      <span><b>${clock(selected.from)} – ${clock(selected.to)}</b> ${t5[selected.level]}</span>
      <span class="spacer"></span>
      <button class="btn small" @click=${this._toggleLevel}>${selected.level === "comfort" ? t5.toNight : t5.toComfort}</button>
      <button class="btn small" @click=${() => this._openCopy("block")}>${t5.copyBlock}</button>
      <button class="btn small danger" @click=${this._remove}>${t5.remove}</button>
      <button class="btn small primary" @click=${this._done}>${t5.done}</button>
    </div>`;
  }
  _copyPanel(t5) {
    const copy = this._copy;
    if (!copy) {
      return A;
    }
    const days = t5.days.split(",");
    const selected = this._selected !== void 0 ? this.week[this.day][this._selected] : void 0;
    const title = copy.kind === "block" && selected ? format(t5.copyBlockTitle, { block: this._describe(this.day, selected, t5) }) : format(t5.copyDayTitle, { day: t5.longDays.split(",")[this.day] });
    const toggle = (day) => {
      const targets = copy.targets.includes(day) ? copy.targets.filter((d3) => d3 !== day) : [...copy.targets, day].sort();
      this._copy = { ...copy, targets };
    };
    const quick = (set) => this._copy = { ...copy, targets: set.filter((d3) => d3 !== this.day) };
    return b2`<div class="card pad copy">
      <div class="small"><b>${title}</b></div>
      <div class="chips">
        ${days.map(
      (name, day) => day === this.day ? A : b2`<button class="chip ${copy.targets.includes(day) ? "selected" : ""}" @click=${() => toggle(day)}>
                ${name}
              </button>`
    )}
      </div>
      <div class="chips">
        <button class="chip" @click=${() => quick(WORKDAYS)}>${t5.workdays}</button>
        <button class="chip" @click=${() => quick(WEEKEND)}>${t5.weekend}</button>
        <button class="chip" @click=${() => quick(ALL_DAYS)}>${t5.all}</button>
      </div>
      ${copy.kind === "day" ? b2`<p class="muted small">${t5.replaces}</p>` : A}
      <div class="actions">
        <span class="spacer"></span>
        <button class="btn" @click=${() => this._copy = void 0}>${t5.cancel}</button>
        <button class="btn primary" ?disabled=${copy.targets.length === 0} @click=${this._doCopy}>
          ${format(t5.copy, { count: String(copy.targets.length) })}
        </button>
      </div>
    </div>`;
  }
  _describe(day, b3, t5) {
    return `${t5.days.split(",")[day]} ${clock(b3.from)}–${clock(b3.to)} ${t5[b3.level]}`;
  }
  _chooseDay(day) {
    this.dispatchEvent(new CustomEvent("cc-day-change", { detail: day }));
  }
  _emit(change) {
    this.dispatchEvent(new CustomEvent("cc-week-change", { detail: change }));
  }
  _tapBlock(event, index) {
    event.stopPropagation();
    if (this._suppressClick || this._selected === index) {
      return;
    }
    this._selected = index;
    this._copy = void 0;
    this._note = void 0;
  }
  _openCopy(kind) {
    this._copy = { kind, targets: [] };
    this._note = void 0;
  }
  _startDrag(event, mode) {
    const index = this._selected;
    if (index === void 0 || this._drag) {
      return;
    }
    event.stopPropagation();
    event.preventDefault();
    const blocks = this.week[this.day];
    const original = blocks[index];
    const { lo, hi } = room(blocks, index);
    const target = event.currentTarget.closest(".block");
    target.setPointerCapture(event.pointerId);
    this._drag = { mode, pointerId: event.pointerId, startY: event.clientY, original, lo, hi, from: original.from, to: original.to };
  }
};
ScheduleTimeline.properties = {
  hass: { attribute: false },
  week: { attribute: false },
  day: { attribute: false },
  _selected: { state: true },
  _drag: { state: true },
  _copy: { state: true },
  _note: { state: true }
};
ScheduleTimeline.styles = [
  sharedStyles,
  i`
      .lvl-comfort {
        background: var(--cc-comfort, #ffb74d);
        color: #3e2700;
      }
      .lvl-night {
        background: var(--cc-night);
        color: #fff;
      }
      .week {
        padding: 6px;
      }
      .weekrow {
        display: grid;
        grid-template-columns: 34px 1fr;
        align-items: center;
        gap: 8px;
        width: 100%;
        border: 0;
        background: transparent;
        color: var(--primary-text-color);
        font: inherit;
        padding: 6px;
        border-radius: 6px;
        cursor: pointer;
      }
      .weekrow.on {
        background: rgba(3, 169, 244, 0.14);
      }
      .wd {
        text-align: left;
      }
      .wd.today {
        color: var(--cc-primary);
        font-weight: 700;
      }
      .mini {
        position: relative;
        height: 10px;
        border-radius: 5px;
        overflow: hidden;
        background: var(--cc-eco-bg, rgba(139, 195, 74, 0.35));
      }
      .mini i {
        position: absolute;
        top: 0;
        bottom: 0;
      }
      .hint {
        margin: 8px 2px;
      }
      .note {
        margin: 8px 2px;
        color: var(--cc-heat);
        font-size: 14px;
      }
      .toolbar {
        position: sticky;
        top: calc(var(--header-height, 56px) + 50px);
        z-index: 6;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
        padding: 8px 12px;
      }
      .copy .chips {
        margin-top: 8px;
        flex-wrap: wrap;
      }
      .actions {
        display: flex;
        gap: 8px;
        align-items: center;
        margin-top: 8px;
      }
      .spacer {
        flex: 1;
      }
      .dayview {
        padding: 10px 8px 14px 0;
      }
      .dayhead {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        padding: 0 4px 8px 12px;
        font-weight: 500;
      }
      .edge {
        margin: 2px 12px 2px 62px;
      }
      .center {
        text-align: center;
      }
      .timeline {
        position: relative;
        margin: 10px 0;
        user-select: none;
        -webkit-user-select: none;
      }
      .hour {
        position: absolute;
        left: 0;
        right: 0;
        border-top: 1px solid var(--cc-divider);
        pointer-events: none;
      }
      .hour span {
        position: absolute;
        top: -8px;
        left: 6px;
        font-size: 11px;
        color: var(--cc-muted);
        background: var(--cc-card);
        padding-right: 4px;
      }
      .lane {
        position: absolute;
        left: 54px;
        right: 8px;
        top: 0;
        bottom: 0;
        background: var(--cc-eco-bg, rgba(139, 195, 74, 0.18));
        border-radius: 6px;
        cursor: copy;
      }
      .block {
        position: absolute;
        left: 4px;
        right: 4px;
        box-sizing: border-box;
        border-radius: 8px;
        padding: 3px 8px;
        font-size: 13px;
        cursor: pointer;
      }
      .block.selected {
        box-shadow: 0 0 0 3px var(--cc-primary);
        z-index: 3;
        touch-action: none;
        cursor: grab;
      }
      .label {
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
      }
      .handle {
        position: absolute;
        left: 50%;
        width: 64px;
        height: 28px;
        margin-left: -32px;
        z-index: 4;
        touch-action: none;
        cursor: ns-resize;
      }
      .handle::after {
        content: "";
        position: absolute;
        left: 10px;
        right: 10px;
        top: 10px;
        height: 8px;
        border-radius: 4px;
        background: var(--cc-primary);
        border: 2px solid var(--cc-card);
      }
      .handle.top {
        top: -14px;
      }
      .handle.bottom {
        bottom: -14px;
      }
      .now {
        position: absolute;
        left: 0;
        right: 0;
        height: 2px;
        background: #e53935;
        z-index: 2;
        pointer-events: none;
      }
      .btn {
        border: 1px solid var(--cc-divider);
        background: transparent;
        color: var(--primary-text-color);
        border-radius: 8px;
        padding: 8px 12px;
        min-height: 36px;
        font: inherit;
        cursor: pointer;
      }
      .btn.small {
        padding: 6px 10px;
        min-height: 32px;
        font-size: 14px;
      }
      .btn.primary {
        background: var(--cc-primary);
        border-color: transparent;
        color: var(--text-primary-color, #fff);
      }
      .btn.danger {
        color: var(--error-color, #d32f2f);
      }
      .btn:disabled {
        opacity: 0.45;
        cursor: default;
      }
    `
];
defineOnce("cc-schedule-timeline", ScheduleTimeline);

// src/rooms/schedule-section.ts
var NEW_SCHEDULE = "__new__";
var TEXTS8 = {
  de: {
    title: "Zeitplan",
    loading: "Lade Zeitpläne …",
    schedule: "Zeitplan",
    none: "– kein Zeitplan –",
    create: "+ Neuen Zeitplan anlegen …",
    noSchedule: "{room} hat keinen Zeitplan und hält Eco.",
    createButton: "Zeitplan anlegen",
    missing: "Der Zeitplan-Helfer {entity} fehlt oder ist nicht verfügbar. {room} hält Eco, bis du einen Zeitplan zuweist oder anlegst.",
    notEditable: "„{name}“ ist nicht in der Oberfläche angelegt (z. B. in YAML) und lässt sich hier nicht bearbeiten. Weise einen anderen Zeitplan zu oder lege einen neuen an.",
    sharedWith: "gilt auch für {rooms}",
    sharedWarning: "Jede Änderung wirkt sofort auf {count} Räume.",
    split: "Für {room} abtrennen",
    comfort: "Komfort",
    night: "Nacht",
    eco: "Eco (außerhalb der Blöcke)",
    saved: "Gespeichert: {change}",
    skipped: "Nicht kopiert nach {days}: überschneidet sich dort mit einem vorhandenen Block.",
    failed: "Nicht gespeichert: ",
    days: "Mo,Di,Mi,Do,Fr,Sa,So",
    orphanQuestion: "„{name}“ gilt für keinen Raum mehr – löschen?",
    delete: "Löschen",
    keep: "Behalten",
    deleted: "„{name}“ gelöscht."
  },
  en: {
    title: "Schedule",
    loading: "Loading schedules …",
    schedule: "Schedule",
    none: "– no schedule –",
    create: "+ Create new schedule …",
    noSchedule: "{room} has no schedule and holds eco.",
    createButton: "Create schedule",
    missing: "The schedule helper {entity} is missing or unavailable. {room} holds eco until you assign or create a schedule.",
    notEditable: "“{name}” was not created in the UI (e.g. in YAML) and cannot be edited here. Assign another schedule or create a new one.",
    sharedWith: "also applies to {rooms}",
    sharedWarning: "Every change applies at once to {count} rooms.",
    split: "Split off for {room}",
    comfort: "Comfort",
    night: "Night",
    eco: "Eco (outside the blocks)",
    saved: "Saved: {change}",
    skipped: "Not copied to {days}: it overlaps a block there.",
    failed: "Not saved: ",
    days: "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
    orphanQuestion: "“{name}” applies to no room any more – delete it?",
    delete: "Delete",
    keep: "Keep",
    deleted: "“{name}” deleted."
  }
};
var RoomScheduleSection = class extends i4 {
  constructor() {
    super(...arguments);
    /** The week as edited but maybe not saved yet, per schedule id. */
    this._edited = /* @__PURE__ */ new Map();
    this._day = today();
    this._saving = /* @__PURE__ */ new Map();
    this._choose = (event) => {
      const select = event.target;
      const room2 = this.room;
      if (!room2) {
        return;
      }
      if (select.value === NEW_SCHEDULE) {
        this._openSheet();
        return;
      }
      void this._assign(room2, { entityId: select.value || null });
    };
    this._deleteOrphan = async () => {
      const orphan = this._orphan;
      if (!this.hass || !orphan) {
        return;
      }
      const t5 = localize(this.hass, TEXTS8);
      this._orphan = void 0;
      try {
        await deleteSchedule(this.hass, orphan.scheduleId);
        this._status = format(t5.deleted, { name: orphan.name });
      } catch (error) {
        this._error = errorMessage(error);
      }
      await this._reload();
    };
  }
  connectedCallback() {
    super.connectedCallback();
    this._subscribe();
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    this._unsubscribe?.then((unsubscribe) => unsubscribe()).catch(() => void 0);
    this._unsubscribe = void 0;
  }
  willUpdate(changed) {
    const previous = changed.get("room");
    if (changed.has("room") && previous?.room_id !== this.room?.room_id) {
      this._day = today();
      this._sheet = void 0;
      this._status = void 0;
    }
  }
  updated(changed) {
    if (changed.has("hass")) {
      this._subscribe();
    }
  }
  _subscribe() {
    if (!this.hass || !this.isConnected || this._unsubscribe) {
      return;
    }
    this._unsubscribe = subscribeAssignments(this.hass, (assignments) => {
      this._assignments = assignments;
      void this._reload();
    });
    this._unsubscribe.catch((error) => {
      this._unsubscribe = void 0;
      this._error = errorMessage(error);
    });
  }
  async _reload() {
    if (!this.hass) {
      return;
    }
    try {
      const items = await listSchedules(this.hass);
      this._items = new Map(items.map((item) => [item.id, item]));
    } catch (error) {
      this._error = errorMessage(error);
    }
  }
  render() {
    const t5 = localize(this.hass, TEXTS8);
    const room2 = this.room;
    const assignments = this._assignments;
    if (!room2 || !assignments || !this._items) {
      return b2`<h2 class="section">${t5.title}</h2>
        <div class="card pad muted small">${this._error ?? t5.loading}</div>`;
    }
    const entityId = assignments.rooms.find((candidate) => candidate.room_id === room2.room_id)?.entity_id ?? null;
    const helper = assignments.schedules.find((candidate) => candidate.entity_id === entityId);
    return b2`
      <h2 class="section">${t5.title}</h2>
      ${this._assignmentCard(room2, entityId, helper, t5)} ${this._body(room2, entityId, helper, t5)}
      ${this._status ? b2`<p class="status small" role="status">${this._status}</p>` : A}
      ${this._orphanCard(t5)} ${this._sheetView(room2)}
    `;
  }
  _assignmentCard(room2, entityId, helper, t5) {
    const schedules = this._assignments?.schedules ?? [];
    const others = entityId ? (this._assignments?.rooms ?? []).filter((r5) => r5.entity_id === entityId && r5.room_id !== room2.room_id) : [];
    const item = this._item(helper);
    return b2`<div class="card pad">
      <label class="field"
        >${t5.schedule}
        <select .value=${l3(entityId ?? "")} @change=${this._choose}>
          <option value="" ?selected=${entityId === null}>${t5.none}</option>
          ${schedules.map(
      (schedule) => b2`<option value=${schedule.entity_id} ?selected=${schedule.entity_id === entityId}>
              ${schedule.name}
            </option>`
    )}
          ${entityId && !helper ? b2`<option value=${entityId} selected>${entityId}</option>` : A}
          <option value=${NEW_SCHEDULE}>${t5.create}</option>
        </select>
      </label>
      ${others.length > 0 ? b2`<div class="shared">
            <div><b>${format(t5.sharedWith, { rooms: others.map((r5) => r5.name).join(", ") })}</b></div>
            <div class="small">${format(t5.sharedWarning, { count: String(others.length + 1) })}</div>
            ${item ? b2`<button class="btn small" @click=${() => this._openSheet(item.id)}>
                  ${format(t5.split, { room: room2.name })}
                </button>` : A}
          </div>` : A}
      ${this._error ? b2`<p class="err" role="alert">${this._error}</p>` : A}
    </div>`;
  }
  _body(room2, entityId, helper, t5) {
    if (entityId === null || !helper) {
      const text = entityId === null ? format(t5.noSchedule, { room: room2.name }) : format(t5.missing, { entity: entityId, room: room2.name });
      return b2`<div class="card pad">
        <p class="muted">${text}</p>
        <button class="btn primary" @click=${() => this._openSheet()}>${t5.createButton}</button>
      </div>`;
    }
    const item = this._item(helper);
    if (!item) {
      return b2`<div class="card pad muted small">${format(t5.notEditable, { name: helper.name })}</div>`;
    }
    return b2`
      ${this._legend(t5)}
      <cc-schedule-timeline
        .hass=${this.hass}
        .week=${this._edited.get(item.id) ?? weekOf(item)}
        .day=${this._day}
        @cc-day-change=${(event) => this._day = event.detail}
        @cc-week-change=${(event) => this._save(item, event.detail)}
      ></cc-schedule-timeline>
    `;
  }
  _legend(t5) {
    return b2`<div class="legend small">
      <span><i class="lvl-comfort"></i>${t5.comfort}</span>
      <span><i class="lvl-night"></i>${t5.night}</span>
      <span><i class="lvl-eco"></i>${t5.eco}</span>
    </div>`;
  }
  _orphanCard(t5) {
    const orphan = this._orphan;
    if (!orphan) {
      return A;
    }
    return b2`<div class="card pad orphan" role="alertdialog">
      <p>${format(t5.orphanQuestion, { name: orphan.name })}</p>
      <div class="actions">
        <span class="spacer"></span>
        <button class="btn" @click=${() => this._orphan = void 0}>${t5.keep}</button>
        <button class="btn danger" @click=${this._deleteOrphan}>${t5.delete}</button>
      </div>
    </div>`;
  }
  _sheetView(room2) {
    const sheet = this._sheet;
    if (!sheet) {
      return A;
    }
    const sources = [...this._items?.values() ?? []].map((item) => ({ id: item.id, name: item.name, week: this._edited.get(item.id) ?? weekOf(item) })).sort((a3, b3) => a3.name.localeCompare(b3.name));
    return b2`<cc-create-schedule-sheet
      .hass=${this.hass}
      .roomName=${room2.name}
      .takenNames=${(this._assignments?.schedules ?? []).map((schedule) => schedule.name)}
      .sources=${sources}
      .preselect=${sheet.preselect}
      .busy=${sheet.busy}
      .error=${sheet.error}
      @cc-cancel=${() => this._sheet = void 0}
      @cc-create=${(event) => this._create(room2, event.detail)}
    ></cc-create-schedule-sheet>`;
  }
  /** The editable item of a helper; undefined for one the native commands do not know. */
  _item(helper) {
    return helper?.schedule_id ? this._items?.get(helper.schedule_id) : void 0;
  }
  _openSheet(preselect) {
    this._sheet = { preselect, busy: false };
  }
  async _assign(room2, schedule) {
    if (!this.hass) {
      return false;
    }
    const previous = this._helperOf(room2.room_id);
    this._error = void 0;
    this._status = void 0;
    try {
      await assignSchedule(this.hass, room2.room_id, schedule);
    } catch (error) {
      this._error = errorMessage(error);
      this.requestUpdate();
      return false;
    }
    this._offerDelete(room2.room_id, previous);
    return true;
  }
  _helperOf(roomId) {
    const entityId = this._assignments?.rooms.find((r5) => r5.room_id === roomId)?.entity_id;
    return this._assignments?.schedules.find((schedule) => schedule.entity_id === entityId);
  }
  /** Ask once to delete the previous schedule of the room when no other room uses it. */
  _offerDelete(roomId, previous) {
    const item = this._item(previous);
    if (!previous || !item) {
      return;
    }
    const stillUsed = this._assignments?.rooms.some((r5) => r5.room_id !== roomId && r5.entity_id === previous.entity_id);
    if (!stillUsed) {
      this._orphan = { scheduleId: item.id, name: item.name };
    }
  }
  async _create(room2, request) {
    const sheet = this._sheet;
    if (!this.hass || !sheet) {
      return;
    }
    this._sheet = { ...sheet, busy: true, error: void 0 };
    let item;
    try {
      item = await createSchedule(this.hass, request.name, scheduleWeekOf(request.week));
    } catch (error) {
      this._sheet = { ...sheet, busy: false, error: errorMessage(error) };
      return;
    }
    this._items = new Map(this._items).set(item.id, item);
    this._sheet = void 0;
    this._day = today();
    await this._assign(room2, { scheduleId: item.id });
  }
  /** Show the change at once, save it after the changes before it. */
  _save(item, change) {
    const hass = this.hass;
    if (!hass) {
      return;
    }
    const t5 = localize(hass, TEXTS8);
    this._edited = new Map(this._edited).set(item.id, change.week);
    const days = t5.days.split(",");
    const skipped = change.skipped?.length ? ` ${format(t5.skipped, { days: change.skipped.map((day) => days[day]).join(", ") })}` : "";
    const before = this._saving.get(item.id) ?? Promise.resolve();
    const saving = before.catch(() => void 0).then(async () => {
      const current = this._items?.get(item.id) ?? item;
      const saved = await updateSchedule(hass, { ...current, ...scheduleWeekOf(change.week) });
      this._items = new Map(this._items).set(saved.id, saved);
      this._status = format(t5.saved, { change: change.label }) + skipped;
    }).catch(async (error) => {
      this._status = t5.failed + errorMessage(error);
      await this._reload();
      throw error;
    }).finally(() => {
      if (this._saving.get(item.id) === saving) {
        this._saving.delete(item.id);
        const edited = new Map(this._edited);
        edited.delete(item.id);
        this._edited = edited;
      }
    });
    this._saving.set(item.id, saving);
    saving.catch(() => void 0);
  }
};
RoomScheduleSection.properties = {
  hass: { attribute: false },
  room: { attribute: false },
  _assignments: { state: true },
  _items: { state: true },
  _edited: { state: true },
  _day: { state: true },
  _sheet: { state: true },
  _orphan: { state: true },
  _status: { state: true },
  _error: { state: true }
};
RoomScheduleSection.styles = [
  sharedStyles,
  i`
      .field {
        display: flex;
        flex-direction: column;
        gap: 4px;
        font-size: 13px;
        color: var(--cc-muted);
      }
      select {
        font: inherit;
        font-size: 16px;
        color: var(--primary-text-color);
        background: var(--primary-background-color, #fafafa);
        border: 1px solid var(--cc-divider);
        border-radius: 8px;
        padding: 9px 10px;
      }
      .shared {
        margin-top: 12px;
        padding: 10px 12px;
        border-radius: 8px;
        background: rgba(230, 81, 0, 0.1);
        border: 1px solid rgba(230, 81, 0, 0.35);
        display: flex;
        flex-direction: column;
        gap: 6px;
        align-items: flex-start;
      }
      .legend {
        display: flex;
        flex-wrap: wrap;
        gap: 14px;
        margin: 4px 2px 10px;
        color: var(--cc-muted);
      }
      .legend span {
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }
      .legend i {
        width: 14px;
        height: 10px;
        border-radius: 3px;
        display: inline-block;
      }
      .lvl-comfort {
        background: var(--cc-comfort, #ffb74d);
      }
      .lvl-night {
        background: var(--cc-night);
      }
      .lvl-eco {
        background: var(--cc-eco-bg, rgba(139, 195, 74, 0.35));
      }
      .status {
        margin: 8px 2px;
        color: var(--cc-muted);
      }
      .orphan {
        border-color: var(--cc-heat);
      }
      .orphan p {
        margin: 0;
      }
      .actions {
        display: flex;
        gap: 8px;
        align-items: center;
        margin-top: 10px;
      }
      .spacer {
        flex: 1;
      }
      .err {
        color: var(--error-color, #d32f2f);
        font-size: 14px;
        margin: 10px 0 0;
      }
      .btn {
        border: 1px solid var(--cc-divider);
        background: transparent;
        color: var(--primary-text-color);
        border-radius: 8px;
        padding: 8px 12px;
        min-height: 36px;
        font: inherit;
        cursor: pointer;
      }
      .btn.small {
        padding: 6px 10px;
        min-height: 32px;
        font-size: 14px;
      }
      .btn.primary {
        background: var(--cc-primary);
        border-color: transparent;
        color: var(--text-primary-color, #fff);
      }
      .btn.danger {
        color: var(--error-color, #d32f2f);
      }
    `
];
defineOnce("cc-room-schedule-section", RoomScheduleSection);

// src/rooms/rooms-tab.ts
var TEXTS9 = {
  de: {
    targetNow: "Soll jetzt",
    noRooms: "Noch keine Räume. Lege sie in den Einstellungen der Integration an."
  },
  en: {
    targetNow: "Target now",
    noRooms: "No rooms yet. Add them in the settings of the integration."
  }
};
var RoomsTab = class extends i4 {
  constructor() {
    super(...arguments);
    this.rooms = [];
  }
  render() {
    const t5 = localize(this.hass, TEXTS9);
    const room2 = this.rooms.find((candidate) => candidate.room_id === this.roomId) ?? this.rooms[0];
    if (!room2) {
      return b2`<p class="muted">${t5.noRooms}</p>`;
    }
    return b2`
      <div class="chips" role="tablist">
        ${this.rooms.map(
      (candidate) => b2`<button
            class="chip ${candidate === room2 ? "selected" : ""}"
            role="tab"
            aria-selected=${candidate === room2}
            @click=${() => navigate(this, "rooms", candidate.room_id)}
          >
            ${candidate.name}
          </button>`
    )}
      </div>
      <div class="card pad">
        <div class="name">${room2.name}</div>
        <div class="muted small">
          ${t5.targetNow} ${formatTemperature(this.hass, room2.target_temperature)} · ${room2.reason ?? ""}
        </div>
      </div>
      <cc-room-schedule-section .hass=${this.hass} .room=${room2}></cc-room-schedule-section>
      <cc-room-levels-section .hass=${this.hass} .room=${room2}></cc-room-levels-section>
    `;
  }
};
RoomsTab.properties = {
  hass: { attribute: false },
  rooms: { attribute: false },
  roomId: { attribute: false }
};
RoomsTab.styles = [
  sharedStyles,
  i`
      .name {
        font-weight: 600;
        margin-bottom: 2px;
      }
    `
];
defineOnce("cc-rooms-tab", RoomsTab);

// src/heating-panel.ts
var TABS = ["overview", "rooms", "house"];
var MENU_ICON = "M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z";
var TEXTS10 = {
  de: {
    title: "Heizung",
    overview: "Übersicht",
    rooms: "Räume",
    house: "Haus",
    menu: "Seitenleiste",
    loading: "Lade Räume …",
    failed: "Die Heizungssteuerung antwortet nicht: {error}"
  },
  en: {
    title: "Heating",
    overview: "Overview",
    rooms: "Rooms",
    house: "House",
    menu: "Sidebar",
    loading: "Loading rooms …",
    failed: "The heating control does not answer: {error}"
  }
};
var HeatingPanel = class extends i4 {
  constructor() {
    super();
    this.narrow = false;
    this._tab = "overview";
    this.addEventListener(NAVIGATE_EVENT, (event) => {
      const { tab, roomId } = event.detail;
      this._tab = tab;
      if (roomId !== void 0) {
        this._roomId = roomId;
      }
    });
  }
  connectedCallback() {
    super.connectedCallback();
    this._subscribe();
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    const unsubscribe = this._unsubscribe;
    this._unsubscribe = void 0;
    unsubscribe?.then((stop) => stop()).catch(() => void 0);
  }
  updated(changed) {
    if (changed.has("hass")) {
      this._subscribe();
    }
  }
  _subscribe() {
    if (!this.hass || !this.isConnected || this._unsubscribe) {
      return;
    }
    this._unsubscribe = subscribeRooms(this.hass, (rooms) => {
      this._rooms = rooms;
      this._error = void 0;
    });
    this._unsubscribe.catch((error) => {
      this._error = format(localize(this.hass, TEXTS10).failed, { error: errorMessage(error) });
    });
  }
  render() {
    const t5 = localize(this.hass, TEXTS10);
    return b2`
      <div class="sticky">
        <header class="toolbar">
          ${this.narrow ? b2`<button class="menu" aria-label=${t5.menu} @click=${this._toggleMenu}>
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d=${MENU_ICON}></path></svg>
              </button>` : A}
          <div class="title">${t5.title}</div>
        </header>
        <nav class="tabs" role="tablist">
          ${TABS.map(
      (tab) => b2`<button
              class="tab ${tab === this._tab ? "selected" : ""}"
              role="tab"
              aria-selected=${tab === this._tab}
              @click=${() => this._tab = tab}
            >
              ${t5[tab]}
            </button>`
    )}
        </nav>
      </div>
      <main>${this._content(t5)}</main>
    `;
  }
  _content(t5) {
    if (this._tab === "house") {
      return b2`<cc-house-tab .hass=${this.hass}></cc-house-tab>`;
    }
    if (this._error) {
      return b2`<p class="error">${this._error}</p>`;
    }
    if (!this._rooms) {
      return b2`<p class="muted">${t5.loading}</p>`;
    }
    if (this._tab === "rooms") {
      return b2`<cc-rooms-tab .hass=${this.hass} .rooms=${this._rooms} .roomId=${this._roomId}></cc-rooms-tab>`;
    }
    return b2`<cc-overview-tab .hass=${this.hass} .rooms=${this._rooms}></cc-overview-tab>`;
  }
  _toggleMenu() {
    this.dispatchEvent(new Event("hass-toggle-menu", { bubbles: true, composed: true }));
  }
};
HeatingPanel.properties = {
  hass: { attribute: false },
  narrow: { type: Boolean },
  _tab: { state: true },
  _roomId: { state: true },
  _rooms: { state: true },
  _error: { state: true }
};
HeatingPanel.styles = [
  sharedStyles,
  i`
      :host {
        display: block;
        min-height: 100%;
        background: var(--primary-background-color, #fafafa);
        color: var(--primary-text-color, #212121);
        font-family: var(--ha-font-family-body, Roboto, system-ui, -apple-system, "Segoe UI", sans-serif);
        font-size: 15px;
        -webkit-tap-highlight-color: transparent;
      }
      .sticky {
        position: sticky;
        top: 0;
        z-index: 5;
      }
      .toolbar {
        display: flex;
        align-items: center;
        gap: 8px;
        height: var(--header-height, 56px);
        padding: 0 12px;
        background: var(--app-header-background-color, var(--cc-primary));
        color: var(--app-header-text-color, #fff);
      }
      .menu {
        display: flex;
        border: 0;
        background: transparent;
        color: inherit;
        padding: 8px;
        border-radius: 50%;
        cursor: pointer;
      }
      .menu svg {
        width: 24px;
        height: 24px;
        fill: currentColor;
      }
      .title {
        font-size: 20px;
        margin-left: 4px;
      }
      .tabs {
        display: flex;
        background: var(--cc-card);
        border-bottom: 1px solid var(--cc-divider);
      }
      .tab {
        flex: 1;
        padding: 12px 8px;
        border: 0;
        border-bottom: 2px solid transparent;
        background: transparent;
        color: var(--cc-muted);
        font: inherit;
        font-weight: 500;
        cursor: pointer;
      }
      .tab.selected {
        color: var(--cc-primary);
        border-bottom-color: var(--cc-primary);
      }
      main {
        max-width: 960px;
        margin: 0 auto;
        padding: 16px 16px calc(96px + env(safe-area-inset-bottom));
      }
      .error {
        color: var(--error-color, #d32f2f);
      }
    `
];
if (!customElements.get("hyggely-panel")) {
  customElements.define("hyggely-panel", HeatingPanel);
}
export {
  HeatingPanel
};
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
lit-html/lit-html.js:
lit-element/lit-element.js:
lit-html/directive.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/directive-helpers.js:
lit-html/directives/live.js:
  (**
   * @license
   * Copyright 2020 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
