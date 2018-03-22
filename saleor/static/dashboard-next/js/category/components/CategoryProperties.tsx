import DeleteIcon from "material-ui-icons/Delete";
import ModeEditIcon from "material-ui-icons/ModeEdit";
import Button from "material-ui/Button";
import Card, { CardActions, CardContent, CardHeader } from "material-ui/Card";
import IconButton from "material-ui/IconButton";
import Typography from "material-ui/Typography";
import * as React from "react";
import { Link } from "react-router-dom";

import PageHeader from "../../components/PageHeader";
import Skeleton from "../../components/Skeleton";
import i18n from "../../i18n";

interface CategoryPropertiesProps {
  description?: string;
  title?: string;
  onBack?();
  onDelete?();
  onEdit?();
}

export const CategoryProperties: React.StatelessComponent<
  CategoryPropertiesProps
> = ({ description, onBack, onDelete, onEdit, title }) => (
  <Card>
    <PageHeader onBack={onBack} title={title}>
      <IconButton onClick={onDelete}>
        <DeleteIcon />
      </IconButton>
      <IconButton onClick={onEdit}>
        <ModeEditIcon />
      </IconButton>
    </PageHeader>
    <CardContent>
      <Typography variant="body1">
        {description !== undefined
          ? description
          : [
              <Skeleton key="skel-1" style={{ width: "80%" }} />,
              <Skeleton key="skel-2" style={{ width: "75%" }} />,
              <Skeleton key="skel-3" style={{ width: "60%" }} />
            ]}
      </Typography>
    </CardContent>
  </Card>
);

export default CategoryProperties;
