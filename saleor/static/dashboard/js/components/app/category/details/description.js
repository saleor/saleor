import React from 'react';
import { Link } from 'react-router-dom';
import Card, { CardContent } from 'material-ui/Card';
import Button from 'material-ui/Button';

import { CardTitle, CardSubtitle, CardActions } from '../../../components/cards';

const description = (props) => (
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

export default description;
