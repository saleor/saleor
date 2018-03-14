import Button from "material-ui/Button";
import Card, { CardActions, CardContent, CardHeader } from "material-ui/Card";
import Typography from "material-ui/Typography";
import * as React from "react";
import { Link } from "react-router-dom";

import Skeleton from "../../components/Skeleton";
import i18n from "../../i18n";

interface CategoryDetailsProps {
  description?: string;
  editButtonLink?: string;
  handleRemoveButtonClick?();
  title?: string;
}

export const CategoryDetails: React.StatelessComponent<
  CategoryDetailsProps
> = ({ description, editButtonLink, handleRemoveButtonClick, title }) => (
  <Card>
    <CardHeader
      title={
        title !== undefined ? title : <Skeleton style={{ width: "10em" }} />
      }
    />
    <CardContent>
      <Typography component="p">
        {description !== undefined
          ? description
          : [
              <Skeleton key="skel-1" style={{ width: "80%" }} />,
              <Skeleton key="skel-2" style={{ width: "75%" }} />,
              <Skeleton key="skel-3" style={{ width: "60%" }} />
            ]}
      </Typography>
    </CardContent>
    <CardActions>
      <Button
        color="secondary"
        component={props => (
          <Link
            to={editButtonLink !== undefined ? editButtonLink : "#"}
            {...props}
          />
        )}
      >
        {i18n.t("Edit", { context: "button" })}
      </Button>
      <Button color="secondary" onClick={handleRemoveButtonClick}>
        {i18n.t("Delete", { context: "button" })}
      </Button>
    </CardActions>
  </Card>
);

export default CategoryDetails;
