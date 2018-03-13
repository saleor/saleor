import Button from "material-ui/Button";
import Card, { CardActions, CardContent, CardHeader } from "material-ui/Card";
import Typography from "material-ui/Typography";
import * as React from "react";
import { Link } from "react-router-dom";

import { Skeleton } from "../../components/Skeleton";
import i18n from "../../i18n";

interface CategoryDetailsProps {
  description: string;
  editButtonLink: string;
  handleRemoveButtonClick?();
  loading: boolean;
  title: string;
}

export const CategoryDetails: React.StatelessComponent<
  CategoryDetailsProps
> = ({
  description,
  editButtonLink,
  handleRemoveButtonClick,
  loading,
  title
}) => (
  <Card>
    <CardHeader
      title={loading ? <Skeleton style={{ width: "10em" }} /> : title}
    />
    <CardContent>
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
        color="secondary"
        component={props => <Link to={editButtonLink} {...props} />}
      >
        {i18n.t("Edit", { context: "button" })}
      </Button>
      <Button color="secondary" onClick={handleRemoveButtonClick}>
        {i18n.t("Delete", { context: "button" })}
      </Button>
    </CardActions>
  </Card>
);
