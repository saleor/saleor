import * as React from "react";
import Button from "material-ui/Button";
import Card, { CardActions, CardContent } from "material-ui/Card";
import Typography from "material-ui/Typography";

import { pgettext } from "../../i18n";

interface DescriptionCardProps {
  description: string;
  descriptionTextLabel?: string;
  editButtonLabel?: string;
  handleEditButtonClick?();
  handleRemoveButtonClick?();
  removeButtonLabel?: string;
  title: string;
}

const defaultProps = {
  description: undefined,
  descriptionTextLabel: pgettext(
    "Description card widget description text label",
    "Description"
  ),
  editButtonLabel: pgettext("Category edit action", "Edit"),
  removeButtonLabel: pgettext("Category list action link", "Remove"),
  title: undefined
};

export const DescriptionCard: React.StatelessComponent<DescriptionCardProps> = (
  props = defaultProps
) => {
  const {
    description,
    descriptionTextLabel,
    editButtonLabel,
    handleEditButtonClick,
    handleRemoveButtonClick,
    removeButtonLabel,
    title
  } = props;
  return (
    <div>
      <Card>
        <CardContent>
          <Typography variant="display1">{title}</Typography>
          <Typography variant="title">{descriptionTextLabel}</Typography>
          <Typography>{description}</Typography>
          <CardActions>
            <Button color="secondary" onClick={handleEditButtonClick}>
              {editButtonLabel}
            </Button>
            <Button color="secondary" onClick={handleRemoveButtonClick}>
              {removeButtonLabel}
            </Button>
          </CardActions>
        </CardContent>
      </Card>
    </div>
  );
};
