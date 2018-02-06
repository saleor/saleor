import React, { Component } from 'react';

import Description from './description';
import Subcategories from './subcategoryList';

class CategoryDetails extends Component {
  render() {
    return (
      <div>
        {this.props.category && (
          <Description category={this.props.category} />
        )}
        <Subcategories
          category={this.props.category}
          categoryChildren={this.props.categoryChildren}
        />
      </div>
    );
  }
}

export default CategoryDetails;
