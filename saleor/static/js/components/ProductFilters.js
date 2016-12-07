import React, { Component, PropTypes } from 'react'
import Relay from 'react-relay';
import queryString from 'query-string';


class ProductFilters extends Component {

  static propTypes = {
    attributes: PropTypes.array,
    onFilterChanged: PropTypes.func.isRequired,
  };

  constructor(props) {
    super(props);
    this.state = {
      filters: {}
    };
  }

  onClick = (attribute, value, event) => {
    const attrValue = `${attribute}:${value}`;
    let url = '';
    const element = event.target;

    this.setState({
      filters: Object.assign(
        this.state.filters,
        {[attrValue]: !this.state.filters[attrValue]})
    });
    const enabled = Object.keys(this.state.filters).filter(key => this.state.filters[key] === true);
    this.props.onFilterChanged(enabled);

    enabled.map((param, index) => {
      param = param.replace(':', '=');
      if (index == 0) {
        url += '?' + param;
      } else {
        url += '&' + param;
      }
    });

    if (enabled.length == 0) {
      url = location.href.split('?')[0];
    }

    history.pushState({}, null , url); 

    if (element.classList.contains('active')) {
      element.classList.remove('active');
    } else {
      element.classList.add('active');
    }
  }

  componentDidMount() {
    let url_params = queryString.parse(location.search);
    Object.keys(url_params).map((params) => {
      let attrValue = '';
      if (Array.isArray(url_params[params])) {
        url_params[params].map((param) => {
          attrValue = `${params}:${param}`;
          this.setState({
            filters: Object.assign(
              this.state.filters,
              {[attrValue]: true})
          });
          const elementID = 'attr'+params+param;
          document.getElementById(elementID).classList.add('active');
        })
      } else {
        attrValue = `${params}:${url_params[params]}`;
        this.setState({
          filters: Object.assign(
            this.state.filters,
            {[attrValue]: true})
        });
        const elementID = 'attr'+params+url_params[params];
        document.getElementById(elementID).classList.add('active');
      }
    })

    const enabled = Object.keys(this.state.filters).filter(key => this.state.filters[key] === true);
    this.props.onFilterChanged(enabled);
  }

  render() {
    const { attributes } = this.props;
    return (
      <div>
        {attributes && (attributes.map((attribute) => {
          return (
            <div key={attribute.id} className="attribute">
              <ul className={attribute.name}>
                <h3>{attribute.display}</h3>
                {attribute.values.map((value) => {
                  const colorStyle = {
                    backgroundColor: value.color
                  }
                  return (
                    <button
                      id={'attr' + attribute.pk+value.pk}
                      key={value.id}
                      className="item"
                      style={colorStyle}
                      onClick={(event) => this.onClick(attribute.pk, value.pk, event)}
                    >
                      {value.display}
                    </button>
                  )
                })}
              </ul>
            </div>
          )
        }))}
      </div>
    )
  }
}

export default Relay.createContainer(ProductFilters, {
  fragments: {
    attributes: () => Relay.QL`
      fragment on ProductAttributeType @relay(plural: true) {
        id
        pk
        name
        display
        values {
          id
          pk
          display
          color
        }
      }
    `,
  },
});
