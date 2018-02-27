import React, { Component } from 'react';
import Button from 'material-ui/Button';
import Card, { CardContent, CardActions } from 'material-ui/Card';
import FilterListIcon from 'material-ui-icons/FilterList';
import PropTypes from 'prop-types';
import grey from 'material-ui/colors/grey';
import { parse as parseQs } from 'qs';
import { withRouter } from 'react-router-dom';
import { withStyles } from 'material-ui/styles';

import { TextField } from '../inputs';
import { createQueryString } from '../../../utils';

const styles = theme => ({
  filterCard: {
    transitionDuration: '200ms',
    [theme.breakpoints.down('sm')]: {
      maxHeight: 76,
      overflow: 'hidden',
    },
  },
  filterCardExpandIconContainer: {
    position: 'absolute',
    top: 21,
    right: 20,
    [theme.breakpoints.up('md')]: {
      display: 'none',
    },
    '& svg': {
      width: 24,
      height: 24,
      fill: '#9e9e9e',
      cursor: 'pointer',
    },
  },
  filterCardContent: {
    position: 'relative',
    borderBottomColor: grey[300],
    borderBottomStyle: 'solid',
    borderBottomWidth: 1,
  },
  filterCardActions: {
    flexDirection: 'row-reverse',
  },
});

class FilterCardComponent extends Component {
  static propTypes = {
    classes: PropTypes.object,
    history: PropTypes.object,
    inputs: PropTypes.arrayOf(PropTypes.shape({
      id: PropTypes.string,
      inputType: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      placeholder: PropTypes.string,
    })).isRequired,
    label: PropTypes.string,
  };

  static defaultProps = {
    label: pgettext('Filter menu label', 'Filters'),
  };

  constructor(props) {
    super(props);
    this.state = {
      collapsed: true,
      formData: parseQs(this.props.location.search.substr(1)),
    };
    this.handleClear = this.handleClear.bind(this);
    this.handleFilterListIconClick = this.handleFilterListIconClick.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
  }

  handleFilterListIconClick() {
    this.setState(prevState => ({ collapsed: !prevState.collapsed }));
  }

  handleSubmit(event) {
    event.preventDefault();
    this.props.history.push({ search: createQueryString(this.props.location.search, this.state.formData) });
  }

  handleInputChange(event) {
    const target = event.target;
    this.setState(prevState => ({
      formData: Object.assign(
        {},
        prevState.formData,
        { [target.name]: target.value },
      ),
    }));
  }

  handleClear() {
    this.setState((prevState) => {
      const formData = Object.keys(prevState.formData)
        .reduce((prev, curr) => Object.assign({}, prev, { [curr]: '' }), {});
      return { formData };
    });
  }

  render() {
    const { label, classes, inputs } = this.props;
    return (
      <Card className={classes.filterCard} style={this.state.collapsed ? {} : { maxHeight: 1000 }}>
        <CardContent className={classes.filterCardContent}>
          <div className={classes.filterCardExpandIconContainer}>
            <FilterListIcon onClick={this.handleFilterListIconClick} />
          </div>
          <CardTitle>{label}</CardTitle>
        </CardContent>
        <form onSubmit={this.handleSubmit}>
          <CardContent>
            {inputs.map((input, inputIndex) => {
              switch (input.inputType) {
                case 'text':
                  return (
                    <TextField
                      key={inputIndex}
                      onChange={this.handleInputChange}
                      value={this.state.formData[input.name] || ''}
                      {...input}
                    />
                  );
              }
            })}
            <CardActions className={classes.filterCardActions}>
              <Button
                color="secondary"
                onClick={this.handleSubmit}
              >
                {pgettext('Filter bar submit', 'Filter')}
              </Button>
              <Button
                color="default"
                onClick={this.handleClear}
              >
                {pgettext('Filter bar clear fields', 'Clear')}
              </Button>
            </CardActions>
          </CardContent>
        </form>
      </Card>
    );
  }
}

const FilterCard = withRouter(withStyles(styles)(FilterCardComponent));

export {
  FilterCard as default,
  FilterCardComponent,
};
