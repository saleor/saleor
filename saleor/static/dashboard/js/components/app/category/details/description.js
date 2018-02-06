import React from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import Card, { CardContent, CardActions } from 'material-ui/Card';
import Button from 'material-ui/Button';

import { CardTitle, CardSubtitle } from '../../../components/cards';

const Component = (props) => (
  <Card>
    <CardContent>
      <CardTitle>
        {props.category.name}
      </CardTitle>
      <CardSubtitle>
        Opis
      </CardSubtitle>
      {props.category.description}
      <CardActions>
        <Link to={`/categories/${props.category.pk}/edit/`}>
          <Button color={'secondary'}>Edytuj</Button>
        </Link>
        <Link to={`/categories/${props.category.parent ? props.category.parent.pk : ''}`}>
          <Button color={'secondary'}>Usuń</Button>
        </Link>
      </CardActions>
    </CardContent>
  </Card>
);
Component.propTypes = {
  category: PropTypes.shape({
    pk: PropTypes.number,
    name: PropTypes.string,
    description: PropTypes.string,
    parent: PropTypes.shape({
      pk: PropTypes.number
    })
  }).isRequired,
  history: PropTypes.object.isRequired
};

export default Component;
