import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import IconButton from "@material-ui/core/IconButton";
import Typography from "@material-ui/core/Typography";
import DeleteIcon from "@material-ui/icons/Delete";
import EditIcon from "@material-ui/icons/Edit";
import * as React from "react";

import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface CategoryPropertiesProps {
  description?: string;
  onEdit?();
  onDelete?();
}

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
