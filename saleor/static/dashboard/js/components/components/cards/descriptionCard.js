import React from 'react';
import Button from 'material-ui/Button';
import Card, { CardActions , CardContent } from 'material-ui/Card';
import PropTypes from 'prop-types';
import Typography from 'material-ui/Typography';
import { Link } from 'react-router-dom';

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
          <Typography variant="display1">
            {title}
          </Typography>
          <Typography variant="title">
            {pgettext('Description card widget description text label', 'Description')}
          </Typography>
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

export default DescriptionCard;
