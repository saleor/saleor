import React, { Component } from 'react';
import Button from 'material-ui/Button';
import Card, { CardContent, CardActions } from 'material-ui/Card';
import FilterListIcon from 'material-ui-icons/FilterList';
import PropTypes from 'prop-types';
import grey from 'material-ui/colors/grey';
import { parse as parseQs } from 'qs';
import { withRouter, Link } from 'react-router-dom';
import { withStyles } from 'material-ui/styles';

import Table from './table';
import { TextField } from './inputs';
import { createQueryString } from '../utils';

const styles = (theme) => ({
  cardTitle: {
    fontWeight: 300,
    fontSize: theme.typography.display1.fontSize
  },
  cardSubtitle: {
    fontSize: theme.typography.title.fontSize,
    lineHeight: '110%',
    margin: '0.65rem 0 0.52rem 0'
  },
  listCard: {
    paddingBottom: 0
  },
  filterCard: {
    transitionDuration: '200ms',
    [theme.breakpoints.down('sm')]: {
      maxHeight: 76,
      overflow: 'hidden'
    }
  },
  listCardActions: {
    paddingBottom: 0
  },
  filterCardExpandIconContainer: {
    position: 'absolute',
    top: 21,
    right: 20,
    [theme.breakpoints.up('md')]: {
      display: 'none'
    },
    '& svg': {
      width: 24,
      height: 24,
      fill: '#9e9e9e',
      cursor: 'pointer'
    }
  },
  filterCardContent: {
    position: 'relative',
    borderBottomColor: grey[300],
    borderBottomStyle: 'solid',
    borderBottomWidth: 1
  },
  filterCardActions: {
    flexDirection: 'row-reverse'
  }
});
const CardTitle = withStyles(styles)(
  (props) => {
    const { classes, children, componentProps } = props;
    return (
      <div className={classes.cardTitle} {...componentProps}>
        {children}
      </div>
    );
  }
);
const CardSubtitle = withStyles(styles)(
  (props) => {
    const { classes, children, componentProps } = props;
    return (
      <div className={classes.cardSubtitle} {...componentProps}>
        {children}
      </div>
    );
  }
);

const DescriptionCard = (props) => {
  const {
    description,
    editButtonHref,
    editButtonLabel,
    handleRemoveButtonClick,
    removeButtonLabel,
    title
  } = props;
  return (
    <div>
      <Card>
        <CardContent>
          <CardTitle>
            {title}
          </CardTitle>
          <CardSubtitle>
            {pgettext('Description card widget description text label', 'Description')}
          </CardSubtitle>
          {description}
          <CardActions>
            <Link to={editButtonHref}>
              <Button color={'secondary'}>
                {editButtonLabel}
              </Button>
            </Link>
            <Button
              color={'secondary'}
              onClick={handleRemoveButtonClick}
            >
              {removeButtonLabel}
            </Button>
          </CardActions>
        </CardContent>
      </Card>
    </div>
  );
};
DescriptionCard.propTypes = {
  description: PropTypes.string,
  editButtonHref: PropTypes.string,
  editButtonLabel: PropTypes.string,
  handleRemoveButtonClick: PropTypes.func,
  removeButtonLabel: PropTypes.string,
  title: PropTypes.string
};

const ListCardComponent = (props) => {
  const {
    addActionLabel,
    classes,
    count,
    displayLabel,
    firstCursor,
    handleAddAction,
    handleChangePage,
    handleChangeRowsPerPage,
    headers,
    href,
    label,
    lastCursor,
    list,
    noDataLabel,
    page,
    rowsPerPage
  } = props;
  return (
    <Card className={classes.listCard}>
      <div>
        {displayLabel && (
          <CardContent className={classes.listCardActions}>
            <CardTitle>
              {label}
            </CardTitle>
            <Button
              color={'secondary'}
              onClick={handleAddAction}
              style={{ margin: '2rem 0 1rem' }}
            >
              {addActionLabel}
            </Button>
          </CardContent>
        )}
        <CardContent style={{
          borderTop: 'none',
          padding: 0
        }}>
          <Table
            count={count}
            handleChangePage={handleChangePage(firstCursor, lastCursor)}
            handleChangeRowsPerPage={handleChangeRowsPerPage}
            headers={headers}
            href={href}
            list={list}
            noDataLabel={noDataLabel}
            page={page}
            rowsPerPage={rowsPerPage}
            rowsPerPageOptions={[2, 5, 10]}
          />
        </CardContent>
      </div>
    </Card>
  );
};
ListCardComponent.propTypes = {
  addActionLabel: PropTypes.string,
  classes: PropTypes.object,
  count: PropTypes.number,
  displayLabel: PropTypes.bool,
  firstCursor: PropTypes.string,
  handleAddAction: PropTypes.func,
  handleChangePage: PropTypes.func,
  handleChangeRowsPerPage: PropTypes.func,
  headers: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string,
    label: PropTypes.string,
    wide: PropTypes.bool
  })),
  href: PropTypes.string,
  label: PropTypes.string,
  lastCursor: PropTypes.string,
  list: PropTypes.array.isRequired,
  noDataLabel: PropTypes.string.isRequired,
  page: PropTypes.number,
  rowsPerPage: PropTypes.number
};
const ListCard = withStyles(styles)(ListCardComponent);

class FilterCardComponent extends Component {
  static propTypes = {
    classes: PropTypes.object,
    history: PropTypes.object,
    inputs: PropTypes.arrayOf(PropTypes.shape({
      id: PropTypes.string,
      inputType: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      placeholder: PropTypes.string
    })).isRequired,
    label: PropTypes.string
  };

  static defaultProps = {
    label: pgettext('Filter menu label', 'Filters')
  };

  constructor(props) {
    super(props);
    this.state = {
      collapsed: true,
      formData: parseQs(this.props.location.search.substr(1))
    };
    this.handleClear = this.handleClear.bind(this);
    this.handleFilterListIconClick = this.handleFilterListIconClick.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
  }

  handleFilterListIconClick() {
    this.setState((prevState) => ({ collapsed: !prevState.collapsed }));
  }

  handleSubmit(event) {
    event.preventDefault();
    this.props.history.push({ search: createQueryString(this.props.location.search, this.state.formData) });
  }

  handleInputChange(event) {
    const target = event.target;
    this.setState((prevState) => {
      return {
        formData: Object.assign(
          {},
          prevState.formData,
          { [target.name]: target.value }
        )
      };
    });
  }

  handleClear() {
    this.setState((prevState) => {
      const formData = Object.keys(prevState.formData)
        .reduce((prev, curr) => {
          return Object.assign({}, prev, { [curr]: '' });
        }, {});
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
  };
}

const FilterCard = withRouter(withStyles(styles)(FilterCardComponent));

export {
  CardSubtitle,
  CardTitle,
  DescriptionCard,
  FilterCard,
  FilterCardComponent,
  ListCard,
  ListCardComponent
};
