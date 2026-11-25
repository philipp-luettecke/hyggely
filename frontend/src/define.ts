// Define a custom element once: a second copy of the module, e.g. after an
// update without reload, must not throw.

export function defineOnce(name: string, element: CustomElementConstructor): void {
  if (!customElements.get(name)) {
    customElements.define(name, element);
  }
}
