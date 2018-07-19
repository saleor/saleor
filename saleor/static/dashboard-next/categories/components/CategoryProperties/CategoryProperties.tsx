import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
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
    <CardTitle
      title={i18n.t("Details")}
      toolbar={
        <>
          <Button variant="flat" color="secondary" onClick={onEdit}>
            {i18n.t("Edit category")}
          </Button>
          <Button variant="flat" color="secondary" onClick={onDelete}>
            {i18n.t("Remove category")}
          </Button>
        </>
      }
    />
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
