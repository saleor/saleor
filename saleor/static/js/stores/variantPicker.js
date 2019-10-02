import { extendObservable } from 'mobx';

class VariantPickerStore {
  constructor() {
    extendObservable(this, {
      variant: {},
      get isEmpty() {
        return !this.variant.id;
      }
    });
  }

  setVariant(variant) {
    this.variant = variant || {};
  }
}

const store = new VariantPickerStore();
export default store;
