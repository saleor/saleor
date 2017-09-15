import { computed, observable } from 'mobx';

class VariantPickerStore {
  @observable variant = {};
  @observable selection = {};

  setVariant(variant) {
    this.variant = variant || {};
  }

  setSelection(selection) {
      this.selection = selection ? selection : {};
  }

  @computed get isEmpty() {
    return !this.variant.id;
  }
}

const store = new VariantPickerStore();
export default store;
