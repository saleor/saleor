import DeleteIcon from "@material-ui/icons/Delete";
import EditIcon from "@material-ui/icons/Edit";
import Card, { CardContent } from "material-ui/Card";
import IconButton from "material-ui/IconButton";
import { withStyles } from "material-ui/styles";
import Typography from "material-ui/Typography";
import * as React from "react";

import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface CategoryPropertiesProps {
  description?: string;
  onEdit?();
  onDelete?();
}

const decorate = withStyles(theme => ({ root: {} }));
const CategoryProperties: React.StatelessComponent<CategoryPropertiesProps> = ({
  description,
  onDelete,
  onEdit
}) => (
  <Card>
    <PageHeader title={i18n.t("Details")}>
      {!!onEdit && (
        <IconButton onClick={onEdit}>
          <EditIcon />
        </IconButton>
      )}
      {!!onDelete && (
        <IconButton onClick={onDelete}>
          <DeleteIcon />
        </IconButton>
      )}
    </PageHeader>
    <CardContent>
      {description === undefined ? (
        <Skeleton />
      ) : (
        <Typography color={description === "" ? "textSecondary" : "default"}>
          {description === "" ? i18n.t("No description") : description}
        </Typography>
      )}
    </CardContent>
  </Card>
);
export default CategoryProperties;
