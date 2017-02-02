import { computed, observable } from 'mobx';

class VariantPickerStore {
  @observable variant = null

  setVariant(variant) {
    this.variant = variant || null;
  }

  @computed get isEmpty() {
    if (this.variant === null) {
      return true;
    }
    return !this.variant.id;
  }
}

const store = new VariantPickerStore();
export default store;
