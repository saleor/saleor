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
        <Subcategories category={this.props.category} children={this.props.children} />
      </div>
    );
  }
}

export default CategoryDetails;
