import React from 'react';
import { Link } from 'react-router-dom';
import Card, { CardContent } from 'material-ui/Card';

import { FlatButton } from '../../../components/buttons';
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
          <FlatButton color={'secondary'}>Edytuj</FlatButton>
        </Link>
        <Link to={`/categories/${props.category.parent ? props.category.parent.pk : ''}`}>
          <FlatButton color={'secondary'}>Usuń</FlatButton>
        </Link>
      </CardActions>
    </CardContent>
  </Card>
);

export default description;
