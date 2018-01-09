import { computed, observable } from 'mobx';

class VariantPickerStore {
  @observable variant = {};

  setVariant(variant) {
    this.variant = variant || {};
  }

  @computed get isEmpty() {
    return !this.variant.id;
  }
}

const store = new VariantPickerStore();
export default store;
