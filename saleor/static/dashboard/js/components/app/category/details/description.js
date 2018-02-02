import React from 'react';
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
        <FlatButton color={'secondary'}>Edytuj</FlatButton>
        <FlatButton color={'secondary'}>Usuń</FlatButton>
      </CardActions>
    </CardContent>
  </Card>
);

export default description;
