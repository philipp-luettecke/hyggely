// node_modules/@lit/reactive-element/css-tag.js
var t = globalThis;
var e = t.ShadowRoot && (void 0 === t.ShadyCSS || t.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype;
var s = Symbol();
var o = /* @__PURE__ */ new WeakMap();
var n = class {
  constructor(t3, e4, o5) {
    if (this._$cssResult$ = true, o5 !== s) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t3, this.t = e4;
  }
  get styleSheet() {
    let t3 = this.o;
    const s4 = this.t;
    if (e && void 0 === t3) {
      const e4 = void 0 !== s4 && 1 === s4.length;
      e4 && (t3 = o.get(s4)), void 0 === t3 && ((this.o = t3 = new CSSStyleSheet()).replaceSync(this.cssText), e4 && o.set(s4, t3));
    }
    return t3;
  }
  toString() {
    return this.cssText;
  }
};
var r = (t3) => new n("string" == typeof t3 ? t3 : t3 + "", void 0, s);
var i = (t3, ...e4) => {
  const o5 = 1 === t3.length ? t3[0] : e4.reduce((e5, s4, o6) => e5 + ((t4) => {
    if (true === t4._$cssResult$) return t4.cssText;
    if ("number" == typeof t4) return t4;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + t4 + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(s4) + t3[o6 + 1], t3[0]);
  return new n(o5, t3, s);
};
var S = (s4, o5) => {
  if (e) s4.adoptedStyleSheets = o5.map((t3) => t3 instanceof CSSStyleSheet ? t3 : t3.styleSheet);
  else for (const e4 of o5) {
    const o6 = document.createElement("style"), n4 = t.litNonce;
    void 0 !== n4 && o6.setAttribute("nonce", n4), o6.textContent = e4.cssText, s4.appendChild(o6);
  }
};
var c = e ? (t3) => t3 : (t3) => t3 instanceof CSSStyleSheet ? ((t4) => {
  let e4 = "";
  for (const s4 of t4.cssRules) e4 += s4.cssText;
  return r(e4);
})(t3) : t3;

// node_modules/@lit/reactive-element/reactive-element.js
var { is: i2, defineProperty: e2, getOwnPropertyDescriptor: h, getOwnPropertyNames: r2, getOwnPropertySymbols: o2, getPrototypeOf: n2 } = Object;
var a = globalThis;
var c2 = a.trustedTypes;
var l = c2 ? c2.emptyScript : "";
var p = a.reactiveElementPolyfillSupport;
var d = (t3, s4) => t3;
var u = { toAttribute(t3, s4) {
  switch (s4) {
    case Boolean:
      t3 = t3 ? l : null;
      break;
    case Object:
    case Array:
      t3 = null == t3 ? t3 : JSON.stringify(t3);
  }
  return t3;
}, fromAttribute(t3, s4) {
  let i5 = t3;
  switch (s4) {
    case Boolean:
      i5 = null !== t3;
      break;
    case Number:
      i5 = null === t3 ? null : Number(t3);
      break;
    case Object:
    case Array:
      try {
        i5 = JSON.parse(t3);
      } catch (t4) {
        i5 = null;
      }
  }
  return i5;
} };
var f = (t3, s4) => !i2(t3, s4);
var b = { attribute: true, type: String, converter: u, reflect: false, useDefault: false, hasChanged: f };
Symbol.metadata ??= Symbol("metadata"), a.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var y = class extends HTMLElement {
  static addInitializer(t3) {
    this._$Ei(), (this.l ??= []).push(t3);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t3, s4 = b) {
    if (s4.state && (s4.attribute = false), this._$Ei(), this.prototype.hasOwnProperty(t3) && ((s4 = Object.create(s4)).wrapped = true), this.elementProperties.set(t3, s4), !s4.noAccessor) {
      const i5 = Symbol(), h3 = this.getPropertyDescriptor(t3, i5, s4);
      void 0 !== h3 && e2(this.prototype, t3, h3);
    }
  }
  static getPropertyDescriptor(t3, s4, i5) {
    const { get: e4, set: r4 } = h(this.prototype, t3) ?? { get() {
      return this[s4];
    }, set(t4) {
      this[s4] = t4;
    } };
    return { get: e4, set(s5) {
      const h3 = e4?.call(this);
      r4?.call(this, s5), this.requestUpdate(t3, h3, i5);
    }, configurable: true, enumerable: true };
  }
  static getPropertyOptions(t3) {
    return this.elementProperties.get(t3) ?? b;
  }
  static _$Ei() {
    if (this.hasOwnProperty(d("elementProperties"))) return;
    const t3 = n2(this);
    t3.finalize(), void 0 !== t3.l && (this.l = [...t3.l]), this.elementProperties = new Map(t3.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(d("finalized"))) return;
    if (this.finalized = true, this._$Ei(), this.hasOwnProperty(d("properties"))) {
      const t4 = this.properties, s4 = [...r2(t4), ...o2(t4)];
      for (const i5 of s4) this.createProperty(i5, t4[i5]);
    }
    const t3 = this[Symbol.metadata];
    if (null !== t3) {
      const s4 = litPropertyMetadata.get(t3);
      if (void 0 !== s4) for (const [t4, i5] of s4) this.elementProperties.set(t4, i5);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t4, s4] of this.elementProperties) {
      const i5 = this._$Eu(t4, s4);
      void 0 !== i5 && this._$Eh.set(i5, t4);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(s4) {
    const i5 = [];
    if (Array.isArray(s4)) {
      const e4 = new Set(s4.flat(1 / 0).reverse());
      for (const s5 of e4) i5.unshift(c(s5));
    } else void 0 !== s4 && i5.push(c(s4));
    return i5;
  }
  static _$Eu(t3, s4) {
    const i5 = s4.attribute;
    return false === i5 ? void 0 : "string" == typeof i5 ? i5 : "string" == typeof t3 ? t3.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = false, this.hasUpdated = false, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    this._$ES = new Promise((t3) => this.enableUpdating = t3), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((t3) => t3(this));
  }
  addController(t3) {
    (this._$EO ??= /* @__PURE__ */ new Set()).add(t3), void 0 !== this.renderRoot && this.isConnected && t3.hostConnected?.();
  }
  removeController(t3) {
    this._$EO?.delete(t3);
  }
  _$E_() {
    const t3 = /* @__PURE__ */ new Map(), s4 = this.constructor.elementProperties;
    for (const i5 of s4.keys()) this.hasOwnProperty(i5) && (t3.set(i5, this[i5]), delete this[i5]);
    t3.size > 0 && (this._$Ep = t3);
  }
  createRenderRoot() {
    const t3 = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return S(t3, this.constructor.elementStyles), t3;
  }
  connectedCallback() {
    this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(true), this._$EO?.forEach((t3) => t3.hostConnected?.());
  }
  enableUpdating(t3) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((t3) => t3.hostDisconnected?.());
  }
  attributeChangedCallback(t3, s4, i5) {
    this._$AK(t3, i5);
  }
  _$ET(t3, s4) {
    const i5 = this.constructor.elementProperties.get(t3), e4 = this.constructor._$Eu(t3, i5);
    if (void 0 !== e4 && true === i5.reflect) {
      const h3 = (void 0 !== i5.converter?.toAttribute ? i5.converter : u).toAttribute(s4, i5.type);
      this._$Em = t3, null == h3 ? this.removeAttribute(e4) : this.setAttribute(e4, h3), this._$Em = null;
    }
  }
  _$AK(t3, s4) {
    const i5 = this.constructor, e4 = i5._$Eh.get(t3);
    if (void 0 !== e4 && this._$Em !== e4) {
      const t4 = i5.getPropertyOptions(e4), h3 = "function" == typeof t4.converter ? { fromAttribute: t4.converter } : void 0 !== t4.converter?.fromAttribute ? t4.converter : u;
      this._$Em = e4;
      const r4 = h3.fromAttribute(s4, t4.type);
      this[e4] = r4 ?? this._$Ej?.get(e4) ?? r4, this._$Em = null;
    }
  }
  requestUpdate(t3, s4, i5, e4 = false, h3) {
    if (void 0 !== t3) {
      const r4 = this.constructor;
      if (false === e4 && (h3 = this[t3]), i5 ??= r4.getPropertyOptions(t3), !((i5.hasChanged ?? f)(h3, s4) || i5.useDefault && i5.reflect && h3 === this._$Ej?.get(t3) && !this.hasAttribute(r4._$Eu(t3, i5)))) return;
      this.C(t3, s4, i5);
    }
    false === this.isUpdatePending && (this._$ES = this._$EP());
  }
  C(t3, s4, { useDefault: i5, reflect: e4, wrapped: h3 }, r4) {
    i5 && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(t3) && (this._$Ej.set(t3, r4 ?? s4 ?? this[t3]), true !== h3 || void 0 !== r4) || (this._$AL.has(t3) || (this.hasUpdated || i5 || (s4 = void 0), this._$AL.set(t3, s4)), true === e4 && this._$Em !== t3 && (this._$Eq ??= /* @__PURE__ */ new Set()).add(t3));
  }
  async _$EP() {
    this.isUpdatePending = true;
    try {
      await this._$ES;
    } catch (t4) {
      Promise.reject(t4);
    }
    const t3 = this.scheduleUpdate();
    return null != t3 && await t3, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ??= this.createRenderRoot(), this._$Ep) {
        for (const [t5, s5] of this._$Ep) this[t5] = s5;
        this._$Ep = void 0;
      }
      const t4 = this.constructor.elementProperties;
      if (t4.size > 0) for (const [s5, i5] of t4) {
        const { wrapped: t5 } = i5, e4 = this[s5];
        true !== t5 || this._$AL.has(s5) || void 0 === e4 || this.C(s5, void 0, i5, e4);
      }
    }
    let t3 = false;
    const s4 = this._$AL;
    try {
      t3 = this.shouldUpdate(s4), t3 ? (this.willUpdate(s4), this._$EO?.forEach((t4) => t4.hostUpdate?.()), this.update(s4)) : this._$EM();
    } catch (s5) {
      throw t3 = false, this._$EM(), s5;
    }
    t3 && this._$AE(s4);
  }
  willUpdate(t3) {
  }
  _$AE(t3) {
    this._$EO?.forEach((t4) => t4.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = true, this.firstUpdated(t3)), this.updated(t3);
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
  shouldUpdate(t3) {
    return true;
  }
  update(t3) {
    this._$Eq &&= this._$Eq.forEach((t4) => this._$ET(t4, this[t4])), this._$EM();
  }
  updated(t3) {
  }
  firstUpdated(t3) {
  }
};
y.elementStyles = [], y.shadowRootOptions = { mode: "open" }, y[d("elementProperties")] = /* @__PURE__ */ new Map(), y[d("finalized")] = /* @__PURE__ */ new Map(), p?.({ ReactiveElement: y }), (a.reactiveElementVersions ??= []).push("2.1.2");

// node_modules/lit-html/lit-html.js
var t2 = globalThis;
var i3 = (t3) => t3;
var s2 = t2.trustedTypes;
var e3 = s2 ? s2.createPolicy("lit-html", { createHTML: (t3) => t3 }) : void 0;
var h2 = "$lit$";
var o3 = `lit$${Math.random().toFixed(9).slice(2)}$`;
var n3 = "?" + o3;
var r3 = `<${n3}>`;
var l2 = document;
var c3 = () => l2.createComment("");
var a2 = (t3) => null === t3 || "object" != typeof t3 && "function" != typeof t3;
var u2 = Array.isArray;
var d2 = (t3) => u2(t3) || "function" == typeof t3?.[Symbol.iterator];
var f2 = "[ 	\n\f\r]";
var v = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g;
var _ = /-->/g;
var m = />/g;
var p2 = RegExp(`>|${f2}(?:([^\\s"'>=/]+)(${f2}*=${f2}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g");
var g = /'/g;
var $ = /"/g;
var y2 = /^(?:script|style|textarea|title)$/i;
var x = (t3) => (i5, ...s4) => ({ _$litType$: t3, strings: i5, values: s4 });
var b2 = x(1);
var w = x(2);
var T = x(3);
var E = Symbol.for("lit-noChange");
var A = Symbol.for("lit-nothing");
var C = /* @__PURE__ */ new WeakMap();
var P = l2.createTreeWalker(l2, 129);
function V(t3, i5) {
  if (!u2(t3) || !t3.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return void 0 !== e3 ? e3.createHTML(i5) : i5;
}
var N = (t3, i5) => {
  const s4 = t3.length - 1, e4 = [];
  let n4, l3 = 2 === i5 ? "<svg>" : 3 === i5 ? "<math>" : "", c4 = v;
  for (let i6 = 0; i6 < s4; i6++) {
    const s5 = t3[i6];
    let a3, u3, d3 = -1, f3 = 0;
    for (; f3 < s5.length && (c4.lastIndex = f3, u3 = c4.exec(s5), null !== u3); ) f3 = c4.lastIndex, c4 === v ? "!--" === u3[1] ? c4 = _ : void 0 !== u3[1] ? c4 = m : void 0 !== u3[2] ? (y2.test(u3[2]) && (n4 = RegExp("</" + u3[2], "g")), c4 = p2) : void 0 !== u3[3] && (c4 = p2) : c4 === p2 ? ">" === u3[0] ? (c4 = n4 ?? v, d3 = -1) : void 0 === u3[1] ? d3 = -2 : (d3 = c4.lastIndex - u3[2].length, a3 = u3[1], c4 = void 0 === u3[3] ? p2 : '"' === u3[3] ? $ : g) : c4 === $ || c4 === g ? c4 = p2 : c4 === _ || c4 === m ? c4 = v : (c4 = p2, n4 = void 0);
    const x2 = c4 === p2 && t3[i6 + 1].startsWith("/>") ? " " : "";
    l3 += c4 === v ? s5 + r3 : d3 >= 0 ? (e4.push(a3), s5.slice(0, d3) + h2 + s5.slice(d3) + o3 + x2) : s5 + o3 + (-2 === d3 ? i6 : x2);
  }
  return [V(t3, l3 + (t3[s4] || "<?>") + (2 === i5 ? "</svg>" : 3 === i5 ? "</math>" : "")), e4];
};
var S2 = class _S {
  constructor({ strings: t3, _$litType$: i5 }, e4) {
    let r4;
    this.parts = [];
    let l3 = 0, a3 = 0;
    const u3 = t3.length - 1, d3 = this.parts, [f3, v2] = N(t3, i5);
    if (this.el = _S.createElement(f3, e4), P.currentNode = this.el.content, 2 === i5 || 3 === i5) {
      const t4 = this.el.content.firstChild;
      t4.replaceWith(...t4.childNodes);
    }
    for (; null !== (r4 = P.nextNode()) && d3.length < u3; ) {
      if (1 === r4.nodeType) {
        if (r4.hasAttributes()) for (const t4 of r4.getAttributeNames()) if (t4.endsWith(h2)) {
          const i6 = v2[a3++], s4 = r4.getAttribute(t4).split(o3), e5 = /([.?@])?(.*)/.exec(i6);
          d3.push({ type: 1, index: l3, name: e5[2], strings: s4, ctor: "." === e5[1] ? I : "?" === e5[1] ? L : "@" === e5[1] ? z : H }), r4.removeAttribute(t4);
        } else t4.startsWith(o3) && (d3.push({ type: 6, index: l3 }), r4.removeAttribute(t4));
        if (y2.test(r4.tagName)) {
          const t4 = r4.textContent.split(o3), i6 = t4.length - 1;
          if (i6 > 0) {
            r4.textContent = s2 ? s2.emptyScript : "";
            for (let s4 = 0; s4 < i6; s4++) r4.append(t4[s4], c3()), P.nextNode(), d3.push({ type: 2, index: ++l3 });
            r4.append(t4[i6], c3());
          }
        }
      } else if (8 === r4.nodeType) if (r4.data === n3) d3.push({ type: 2, index: l3 });
      else {
        let t4 = -1;
        for (; -1 !== (t4 = r4.data.indexOf(o3, t4 + 1)); ) d3.push({ type: 7, index: l3 }), t4 += o3.length - 1;
      }
      l3++;
    }
  }
  static createElement(t3, i5) {
    const s4 = l2.createElement("template");
    return s4.innerHTML = t3, s4;
  }
};
function M(t3, i5, s4 = t3, e4) {
  if (i5 === E) return i5;
  let h3 = void 0 !== e4 ? s4._$Co?.[e4] : s4._$Cl;
  const o5 = a2(i5) ? void 0 : i5._$litDirective$;
  return h3?.constructor !== o5 && (h3?._$AO?.(false), void 0 === o5 ? h3 = void 0 : (h3 = new o5(t3), h3._$AT(t3, s4, e4)), void 0 !== e4 ? (s4._$Co ??= [])[e4] = h3 : s4._$Cl = h3), void 0 !== h3 && (i5 = M(t3, h3._$AS(t3, i5.values), h3, e4)), i5;
}
var R = class {
  constructor(t3, i5) {
    this._$AV = [], this._$AN = void 0, this._$AD = t3, this._$AM = i5;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t3) {
    const { el: { content: i5 }, parts: s4 } = this._$AD, e4 = (t3?.creationScope ?? l2).importNode(i5, true);
    P.currentNode = e4;
    let h3 = P.nextNode(), o5 = 0, n4 = 0, r4 = s4[0];
    for (; void 0 !== r4; ) {
      if (o5 === r4.index) {
        let i6;
        2 === r4.type ? i6 = new k(h3, h3.nextSibling, this, t3) : 1 === r4.type ? i6 = new r4.ctor(h3, r4.name, r4.strings, this, t3) : 6 === r4.type && (i6 = new Z(h3, this, t3)), this._$AV.push(i6), r4 = s4[++n4];
      }
      o5 !== r4?.index && (h3 = P.nextNode(), o5++);
    }
    return P.currentNode = l2, e4;
  }
  p(t3) {
    let i5 = 0;
    for (const s4 of this._$AV) void 0 !== s4 && (void 0 !== s4.strings ? (s4._$AI(t3, s4, i5), i5 += s4.strings.length - 2) : s4._$AI(t3[i5])), i5++;
  }
};
var k = class _k {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(t3, i5, s4, e4) {
    this.type = 2, this._$AH = A, this._$AN = void 0, this._$AA = t3, this._$AB = i5, this._$AM = s4, this.options = e4, this._$Cv = e4?.isConnected ?? true;
  }
  get parentNode() {
    let t3 = this._$AA.parentNode;
    const i5 = this._$AM;
    return void 0 !== i5 && 11 === t3?.nodeType && (t3 = i5.parentNode), t3;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t3, i5 = this) {
    t3 = M(this, t3, i5), a2(t3) ? t3 === A || null == t3 || "" === t3 ? (this._$AH !== A && this._$AR(), this._$AH = A) : t3 !== this._$AH && t3 !== E && this._(t3) : void 0 !== t3._$litType$ ? this.$(t3) : void 0 !== t3.nodeType ? this.T(t3) : d2(t3) ? this.k(t3) : this._(t3);
  }
  O(t3) {
    return this._$AA.parentNode.insertBefore(t3, this._$AB);
  }
  T(t3) {
    this._$AH !== t3 && (this._$AR(), this._$AH = this.O(t3));
  }
  _(t3) {
    this._$AH !== A && a2(this._$AH) ? this._$AA.nextSibling.data = t3 : this.T(l2.createTextNode(t3)), this._$AH = t3;
  }
  $(t3) {
    const { values: i5, _$litType$: s4 } = t3, e4 = "number" == typeof s4 ? this._$AC(t3) : (void 0 === s4.el && (s4.el = S2.createElement(V(s4.h, s4.h[0]), this.options)), s4);
    if (this._$AH?._$AD === e4) this._$AH.p(i5);
    else {
      const t4 = new R(e4, this), s5 = t4.u(this.options);
      t4.p(i5), this.T(s5), this._$AH = t4;
    }
  }
  _$AC(t3) {
    let i5 = C.get(t3.strings);
    return void 0 === i5 && C.set(t3.strings, i5 = new S2(t3)), i5;
  }
  k(t3) {
    u2(this._$AH) || (this._$AH = [], this._$AR());
    const i5 = this._$AH;
    let s4, e4 = 0;
    for (const h3 of t3) e4 === i5.length ? i5.push(s4 = new _k(this.O(c3()), this.O(c3()), this, this.options)) : s4 = i5[e4], s4._$AI(h3), e4++;
    e4 < i5.length && (this._$AR(s4 && s4._$AB.nextSibling, e4), i5.length = e4);
  }
  _$AR(t3 = this._$AA.nextSibling, s4) {
    for (this._$AP?.(false, true, s4); t3 !== this._$AB; ) {
      const s5 = i3(t3).nextSibling;
      i3(t3).remove(), t3 = s5;
    }
  }
  setConnected(t3) {
    void 0 === this._$AM && (this._$Cv = t3, this._$AP?.(t3));
  }
};
var H = class {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t3, i5, s4, e4, h3) {
    this.type = 1, this._$AH = A, this._$AN = void 0, this.element = t3, this.name = i5, this._$AM = e4, this.options = h3, s4.length > 2 || "" !== s4[0] || "" !== s4[1] ? (this._$AH = Array(s4.length - 1).fill(new String()), this.strings = s4) : this._$AH = A;
  }
  _$AI(t3, i5 = this, s4, e4) {
    const h3 = this.strings;
    let o5 = false;
    if (void 0 === h3) t3 = M(this, t3, i5, 0), o5 = !a2(t3) || t3 !== this._$AH && t3 !== E, o5 && (this._$AH = t3);
    else {
      const e5 = t3;
      let n4, r4;
      for (t3 = h3[0], n4 = 0; n4 < h3.length - 1; n4++) r4 = M(this, e5[s4 + n4], i5, n4), r4 === E && (r4 = this._$AH[n4]), o5 ||= !a2(r4) || r4 !== this._$AH[n4], r4 === A ? t3 = A : t3 !== A && (t3 += (r4 ?? "") + h3[n4 + 1]), this._$AH[n4] = r4;
    }
    o5 && !e4 && this.j(t3);
  }
  j(t3) {
    t3 === A ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t3 ?? "");
  }
};
var I = class extends H {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t3) {
    this.element[this.name] = t3 === A ? void 0 : t3;
  }
};
var L = class extends H {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t3) {
    this.element.toggleAttribute(this.name, !!t3 && t3 !== A);
  }
};
var z = class extends H {
  constructor(t3, i5, s4, e4, h3) {
    super(t3, i5, s4, e4, h3), this.type = 5;
  }
  _$AI(t3, i5 = this) {
    if ((t3 = M(this, t3, i5, 0) ?? A) === E) return;
    const s4 = this._$AH, e4 = t3 === A && s4 !== A || t3.capture !== s4.capture || t3.once !== s4.once || t3.passive !== s4.passive, h3 = t3 !== A && (s4 === A || e4);
    e4 && this.element.removeEventListener(this.name, this, s4), h3 && this.element.addEventListener(this.name, this, t3), this._$AH = t3;
  }
  handleEvent(t3) {
    "function" == typeof this._$AH ? this._$AH.call(this.options?.host ?? this.element, t3) : this._$AH.handleEvent(t3);
  }
};
var Z = class {
  constructor(t3, i5, s4) {
    this.element = t3, this.type = 6, this._$AN = void 0, this._$AM = i5, this.options = s4;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t3) {
    M(this, t3);
  }
};
var B = t2.litHtmlPolyfillSupport;
B?.(S2, k), (t2.litHtmlVersions ??= []).push("3.3.3");
var D = (t3, i5, s4) => {
  const e4 = s4?.renderBefore ?? i5;
  let h3 = e4._$litPart$;
  if (void 0 === h3) {
    const t4 = s4?.renderBefore ?? null;
    e4._$litPart$ = h3 = new k(i5.insertBefore(c3(), t4), t4, void 0, s4 ?? {});
  }
  return h3._$AI(t3), h3;
};

// node_modules/lit-element/lit-element.js
var s3 = globalThis;
var i4 = class extends y {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const t3 = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= t3.firstChild, t3;
  }
  update(t3) {
    const r4 = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t3), this._$Do = D(r4, this.renderRoot, this.renderOptions);
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
    { type: "climate_control/rooms/subscribe" }
  );
}
function returnToAuto(hass, roomId) {
  return hass.callWS({
    type: "climate_control/room/return_to_auto",
    room_id: roomId
  });
}

// src/api/levels.ts
function getRoomLevels(hass, roomId) {
  return hass.callWS({ type: "climate_control/room/levels", room_id: roomId });
}
function setRoomLevels(hass, roomId, changes) {
  return hass.callWS({
    type: "climate_control/room/set_levels",
    room_id: roomId,
    ...changes
  });
}
function getGlobalTemperatures(hass) {
  return hass.callWS({ type: "climate_control/house/temperatures" });
}
function setGlobalTemperatures(hass, changes) {
  return hass.callWS({ type: "climate_control/house/set_temperatures", ...changes });
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
function stepLeadTime(minutes, direction) {
  const steps = minutes / LEAD_TIME_STEP_MINUTES;
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
    const t3 = localize(this.hass, TEXTS);
    return b2`<h2 class="section">${t3.title}</h2>
      <div class="card pad">${this._body(t3)}</div>`;
  }
  _body(t3) {
    if (!this._temperatures) {
      return this._error ? b2`<p class="error" role="alert">${this._error}</p>` : b2`<span class="muted small">${t3.loading}</span>`;
    }
    const temperatures = { ...this._temperatures, ...this._save.changes };
    return b2`
      ${GLOBAL_LEVELS.map((level) => {
      const key = `${level}_temperature`;
      const value = temperatures[key];
      return stepper({
        label: t3[level],
        value: formatTemperature(this.hass, value),
        less: format(t3.less, { name: t3[level] }),
        more: format(t3.more, { name: t3[level] }),
        canDown: value > MIN_TEMPERATURE,
        canUp: value < MAX_TEMPERATURE,
        onStep: (direction) => {
          this._error = void 0;
          this._save.change({ [key]: stepTemperature(value, direction) });
          this.requestUpdate();
        }
      });
    })}
      <p class="muted small">${t3.frostNote}</p>
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
    type: "climate_control/house/subscribe"
  });
}
function setHouseMode(hass, houseMode) {
  return hass.callWS({ type: "climate_control/house/set_mode", house_mode: houseMode });
}
function startVacation(hass, end) {
  return hass.callWS({ type: "climate_control/house/start_vacation", end });
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
      const t3 = localize(this.hass, TEXTS2);
      this._sheet = { ...sheet, busy: true, error: void 0 };
      try {
        await startVacation(this.hass, `${sheet.date}T${sheet.time}`);
        this._sheet = void 0;
      } catch (error) {
        const code = error?.code;
        this._sheet = {
          ...sheet,
          busy: false,
          error: code === VACATION_END_MUST_BE_AHEAD ? t3.endNotAhead : t3.failed + errorMessage(error)
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
    const t3 = localize(this.hass, TEXTS2);
    const house = this._house;
    if (!house) {
      return b2`<h2 class="section">${t3.title}</h2>
        <div class="card pad muted small">${this._error ?? t3.loading}</div>`;
    }
    return b2`
      <h2 class="section">${t3.title}</h2>
      ${this._modeCard(house, t3)} ${this._awayCard(house, t3)} ${this._vacationSheet(house, t3)}
    `;
  }
  _modeCard(house, t3) {
    const explain = {
      auto: t3.explainAuto,
      vacation: t3.explainVacation,
      off: t3.explainOff
    }[house.house_mode];
    return b2`<div class="card pad">
      <div class="seg" role="group" aria-label=${t3.title}>
        ${MODES.map(
      (mode) => b2`<button
            class=${house.house_mode === mode ? "on" : ""}
            aria-pressed=${house.house_mode === mode ? "true" : "false"}
            @click=${() => this._choose(mode)}
          >
            ${t3[mode]}
          </button>`
    )}
      </div>
      <p class="muted small">${explain} ${t3.overrideStillWorks}</p>
      ${house.house_mode === "vacation" && house.vacation_end ? b2`<div class="row-between">
            <span
              >${t3.vacationUntil}
              <b>${formatVacationEnd(language(this.hass), house.vacation_end)}</b>${t3.thenAuto}</span
            >
            <button class="btn" @click=${this._openSheet}>${t3.changeEnd}</button>
          </div>` : A}
      ${this._error ? b2`<p class="err" role="alert">${this._error}</p>` : A}
    </div>`;
  }
  _awayCard(house, t3) {
    return b2`<div class="card pad">
      <div class="row-between">
        <b>${t3.awayTitle}</b>
        <span class="chip static ${house.away ? "selected warn" : ""}">
          ${house.away ? t3.yes : t3.no}
        </span>
      </div>
      <p class="muted small">${house.away ? t3.awayNow : t3.notAway} ${t3.awayExplain}</p>
      ${house.persons.length === 0 ? b2`<p class="muted small">${t3.noPersons}</p>` : b2`<ul class="persons">
            ${house.persons.map(
      (person) => b2`<li>
                <span>${person.name}</span>
                <span class="presence presence-${person.presence}"
                  >${t3[person.presence]}</span
                >
              </li>`
    )}
          </ul>`}
    </div>`;
  }
  _vacationSheet(house, t3) {
    const sheet = this._sheet;
    if (!sheet) {
      return A;
    }
    const onVacation = house.house_mode === "vacation";
    return b2`<div class="sheet-root">
      <div class="backdrop" @click=${this._closeSheet}></div>
      <div class="sheet" role="dialog" aria-modal="true" aria-labelledby="sheet-title">
        <h3 id="sheet-title">${onVacation ? t3.sheetChange : t3.sheetStart}</h3>
        <p class="muted small">${t3.sheetHint}</p>
        <div class="field-row">
          <label
            >${t3.endDate}
            <input
              type="date"
              .value=${sheet.date}
              @input=${(event) => this._editSheet({ date: event.target.value })}
          /></label>
          <label
            >${t3.endTime}
            <input
              type="time"
              .value=${sheet.time}
              @input=${(event) => this._editSheet({ time: event.target.value })}
          /></label>
        </div>
        ${sheet.error ? b2`<p class="err" role="alert">${sheet.error}</p>` : A}
        <div class="sheet-actions">
          <span class="spacer"></span>
          <button class="btn" @click=${this._closeSheet}>${t3.cancel}</button>
          <button
            class="btn primary"
            ?disabled=${sheet.busy || !sheet.date || !sheet.time}
            @click=${this._submitSheet}
          >
            ${onVacation ? t3.save : t3.start}
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
    const t3 = localize(this.hass, TEXTS2);
    setHouseMode(this.hass, mode).catch((error) => {
      this._error = t3.failed + errorMessage(error);
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
    const t3 = localize(this.hass, TEXTS3);
    const mode = house.house_mode === "vacation" && house.vacation_end ? format(t3.vacation, { end: formatVacationEnd(language(this.hass), house.vacation_end) }) : house.house_mode === "off" ? t3.off : t3.auto;
    return b2`<div class="chips">
      <button
        class="chip ${house.house_mode === "auto" ? "" : "selected warn"}"
        @click=${this._openHouse}
      >
        ${mode}
      </button>
      <button class="chip ${house.away ? "selected warn" : ""}" @click=${this._openHouse}>
        ${house.away ? t3.away : t3.someoneHome}
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
        const t3 = localize(this.hass, TEXTS4);
        this._error = format(t3.failed, { room: pending.name, error: errorMessage(error) });
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
    const t3 = localize(this.hass, TEXTS4);
    return b2`
      <cc-house-status .hass=${this.hass}></cc-house-status>
      ${this.rooms.length === 0 ? b2`<p class="muted">${t3.noRooms}</p>` : A}
      <div class="grid">${this.rooms.map((room) => this._card(room, t3))}</div>
      ${this._toast(t3)}
    `;
  }
  _card(room, t3) {
    const pending = this._pending?.roomId === room.room_id;
    const mode = pending ? "auto" : room.room_mode;
    const colour = REASON_COLOURS[room.reason_code ?? ""] ?? "auto";
    let foot = A;
    if (pending) {
      foot = t3.pending;
    } else if (room.room_mode === "heat") {
      foot = t3.endOverride;
    } else if (room.room_mode === "off") {
      foot = t3.endOff;
    }
    return b2`
      <div
        class="card room colour-${colour} ${pending ? "pending" : ""}"
        role="button"
        tabindex="0"
        @click=${() => this._tap(room)}
        @keydown=${(event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        this._tap(room);
      }
    }}
      >
        <div class="top">
          <span class="name">${room.name}</span>
          <span class="mode mode-${mode}">${t3[mode]}</span>
        </div>
        <div class="temps">
          <span class="current">${formatTemperature(this.hass, room.current_temperature)}</span>
          <span class="target">
            <span class="muted">${t3.target}</span>
            ${formatTemperature(this.hass, room.target_temperature)}
          </span>
        </div>
        <div class="reason">${room.reason ?? ""}</div>
        <div class="foot ${pending ? "muted" : ""}">${foot}</div>
      </div>
    `;
  }
  _toast(t3) {
    if (this._pending) {
      return b2`<div class="toast" role="status">
        <span>${format(t3.returning, { room: this._pending.name })}</span>
        <button @click=${this._undo}>${t3.undo}</button>
      </div>`;
    }
    if (this._error) {
      return b2`<div class="toast" role="alert">
        <span>${this._error}</span>
        <button @click=${() => this._error = void 0}>${t3.dismiss}</button>
      </div>`;
    }
    return A;
  }
  _tap(room) {
    if (room.room_mode === "auto" || this._pending?.roomId === room.room_id) {
      return;
    }
    this._sendPending();
    this._error = void 0;
    this._pending = {
      roomId: room.room_id,
      name: room.name,
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
function formatLeadTime(minutes) {
  const total = Math.round(minutes);
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
    const t3 = localize(this.hass, TEXTS5);
    return b2`<h2 class="section">${t3.title}</h2>
      <div class="card pad">${this._body(t3)}</div>`;
  }
  _body(t3) {
    if (!this._levels) {
      return this._error ? b2`<p class="error" role="alert">${this._error}</p>` : b2`<span class="muted small">${t3.loading}</span>`;
    }
    const levels = { ...this._levels, ...this._save?.changes };
    const warmer = ["night", "eco"].filter(
      (level) => levels[`${level}_temperature`] > levels.comfort_temperature
    );
    return b2`
      ${LEVELS.map((level) => this._temperatureRow(t3, levels, level))}
      ${warmer.map(
      (level) => b2`<p class="hint small" role="status">${format(t3.warmer, { level: t3[level] })}</p>`
    )}
      ${stepper({
      label: t3.leadTime,
      value: formatLeadTime(levels.lead_time_minutes),
      less: format(t3.less, { name: t3.leadTime }),
      more: format(t3.more, { name: t3.leadTime }),
      canDown: levels.lead_time_minutes > 0,
      canUp: levels.lead_time_minutes < MAX_LEAD_TIME_MINUTES,
      onStep: (direction) => this._change({ lead_time_minutes: stepLeadTime(levels.lead_time_minutes, direction) })
    })}
      <p class="muted small note">${t3.leadTimeNote}</p>
      ${this._error ? b2`<p class="error small" role="alert">${this._error}</p>` : A}
    `;
  }
  _temperatureRow(t3, levels, level) {
    const key = `${level}_temperature`;
    const value = levels[key];
    return stepper({
      label: b2`<i class="dot dot-${level}"></i>${t3[level]}`,
      value: formatTemperature(this.hass, value),
      less: format(t3.less, { name: t3[level] }),
      more: format(t3.more, { name: t3[level] }),
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

// src/placeholder.ts
var TEXTS6 = {
  de: { later: "Folgt in einer späteren Version." },
  en: { later: "Coming in a later version." }
};
function placeholderSection(hass, title) {
  return b2`<h2 class="section">${title}</h2>
    <div class="card pad muted small">${localize(hass, TEXTS6).later}</div>`;
}

// src/rooms/schedule-section.ts
var TEXTS7 = {
  de: { title: "Zeitplan" },
  en: { title: "Schedule" }
};
var RoomScheduleSection = class extends i4 {
  render() {
    return placeholderSection(this.hass, localize(this.hass, TEXTS7).title);
  }
};
RoomScheduleSection.properties = {
  hass: { attribute: false },
  room: { attribute: false }
};
RoomScheduleSection.styles = sharedStyles;
defineOnce("cc-room-schedule-section", RoomScheduleSection);

// src/rooms/rooms-tab.ts
var TEXTS8 = {
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
    const t3 = localize(this.hass, TEXTS8);
    const room = this.rooms.find((candidate) => candidate.room_id === this.roomId) ?? this.rooms[0];
    if (!room) {
      return b2`<p class="muted">${t3.noRooms}</p>`;
    }
    return b2`
      <div class="chips" role="tablist">
        ${this.rooms.map(
      (candidate) => b2`<button
            class="chip ${candidate === room ? "selected" : ""}"
            role="tab"
            aria-selected=${candidate === room}
            @click=${() => navigate(this, "rooms", candidate.room_id)}
          >
            ${candidate.name}
          </button>`
    )}
      </div>
      <div class="card pad">
        <div class="name">${room.name}</div>
        <div class="muted small">
          ${t3.targetNow} ${formatTemperature(this.hass, room.target_temperature)} · ${room.reason ?? ""}
        </div>
      </div>
      <cc-room-schedule-section .hass=${this.hass} .room=${room}></cc-room-schedule-section>
      <cc-room-levels-section .hass=${this.hass} .room=${room}></cc-room-levels-section>
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
var TEXTS9 = {
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
      this._error = format(localize(this.hass, TEXTS9).failed, { error: errorMessage(error) });
    });
  }
  render() {
    const t3 = localize(this.hass, TEXTS9);
    return b2`
      <div class="sticky">
        <header class="toolbar">
          ${this.narrow ? b2`<button class="menu" aria-label=${t3.menu} @click=${this._toggleMenu}>
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d=${MENU_ICON}></path></svg>
              </button>` : A}
          <div class="title">${t3.title}</div>
        </header>
        <nav class="tabs" role="tablist">
          ${TABS.map(
      (tab) => b2`<button
              class="tab ${tab === this._tab ? "selected" : ""}"
              role="tab"
              aria-selected=${tab === this._tab}
              @click=${() => this._tab = tab}
            >
              ${t3[tab]}
            </button>`
    )}
        </nav>
      </div>
      <main>${this._content(t3)}</main>
    `;
  }
  _content(t3) {
    if (this._tab === "house") {
      return b2`<cc-house-tab .hass=${this.hass}></cc-house-tab>`;
    }
    if (this._error) {
      return b2`<p class="error">${this._error}</p>`;
    }
    if (!this._rooms) {
      return b2`<p class="muted">${t3.loading}</p>`;
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
if (!customElements.get("climate-control-panel")) {
  customElements.define("climate-control-panel", HeatingPanel);
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
*/
