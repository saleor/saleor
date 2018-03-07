import * as React from "react";
import Button from "material-ui/Button";
import Card, { CardActions, CardContent } from "material-ui/Card";
import Typography from "material-ui/Typography";
import { Link } from "react-router-dom";

import { pgettext } from "../../i18n";
import { Skeleton } from "../Skeleton";

interface DescriptionCardProps {
  description: string;
  editButtonLabel?: string;
  editButtonLink: string;
  handleRemoveButtonClick?();
  loading: boolean;
  removeButtonLabel?: string;
  title: string;
}

export const DescriptionCard: React.StatelessComponent<
  DescriptionCardProps
> = ({
  description,
  editButtonLabel,
  editButtonLink,
  handleRemoveButtonClick,
  loading,
  removeButtonLabel,
  title
}) => (
  <Card>
    <CardContent>
      <Typography variant="headline" component="h2">
        {loading ? <Skeleton style={{ width: "10em" }} /> : title}
      </Typography>
      <Typography component="p">
        {loading
          ? [
              <Skeleton key="skel-1" style={{ width: "80%" }} />,
              <Skeleton key="skel-2" style={{ width: "75%" }} />,
              <Skeleton key="skel-3" style={{ width: "60%" }} />
            ]
          : description}
      </Typography>
    </CardContent>
    <CardActions>
      <Button
        color="primary"
        component={props => <Link to={editButtonLink} {...props} />}
      >
        {editButtonLabel}
      </Button>
      <Button color="primary" onClick={handleRemoveButtonClick}>
        {removeButtonLabel}
      </Button>
    </CardActions>
  </Card>
);
DescriptionCard.defaultProps = {
  editButtonLabel: pgettext("Category edit action", "Edit"),
  removeButtonLabel: pgettext("Category list action link", "Remove")
};
