import $ from 'jquery';
import { observer } from 'mobx-react';
import React, { Component, PropTypes } from 'react';

@observer
export default class ProductSchema extends Component {

  static propTypes = {
    variantStore: PropTypes.object.isRequired,
    productSchema: PropTypes.object
  };

  getSchema = () => {
    const { variantStore, productSchema } = this.props;
    let variant = variantStore.variant;
    if (!variantStore.isEmpty){
      let variantSchema = $.extend({}, productSchema);
      variantSchema['offers'] = variant.schemaData;
      return JSON.stringify(variantSchema);
    }else{
      return JSON.stringify(productSchema);
    }
  };

  render() {
    let body = this.getSchema();
    return (
      <script type="application/ld+json">{ body }</script>
    )
  }
}
