import * as React from "react";
import Button from "material-ui/Button";
import Card, { CardActions, CardContent } from "material-ui/Card";
import Typography from "material-ui/Typography";

import { pgettext } from "../../i18n";
import { loadavg } from "os";
import { Skeleton } from "../Skeleton";

interface DescriptionCardProps {
  description: string;
  descriptionTextLabel?: string;
  editButtonLabel?: string;
  handleEditButtonClick?();
  handleRemoveButtonClick?();
  loading: boolean;
  removeButtonLabel?: string;
  title: string;
}

export const DescriptionCard: React.StatelessComponent<
  DescriptionCardProps
> = ({
  description,
  descriptionTextLabel,
  editButtonLabel,
  handleEditButtonClick,
  handleRemoveButtonClick,
  loading,
  removeButtonLabel,
  title
}) => (
  <div>
    <Card>
      <CardContent>
        <Typography variant="display1">
          {loading ? <Skeleton style={{ width: "10em" }} /> : title}
        </Typography>
        <Typography variant="title">{descriptionTextLabel}</Typography>
        <Typography>
          {loading
            ? [
                <Skeleton key="skel-1" style={{ width: "80%" }} />,
                <Skeleton key="skel-1" style={{ width: "75%" }} />,
                <Skeleton key="skel-1" style={{ width: "60%" }} />
              ]
            : description}
        </Typography>
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
DescriptionCard.defaultProps = {
  descriptionTextLabel: pgettext(
    "Description card widget description text label",
    "Description"
  ),
  editButtonLabel: pgettext("Category edit action", "Edit"),
  removeButtonLabel: pgettext("Category list action link", "Remove")
};
