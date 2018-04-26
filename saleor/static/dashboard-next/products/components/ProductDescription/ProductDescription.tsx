import DeleteIcon from "@material-ui/icons/Delete";
import EditIcon from "@material-ui/icons/Edit";
import VisibilityIcon from "@material-ui/icons/Visibility";
import Card, { CardContent } from "material-ui/Card";
import IconButton from "material-ui/IconButton";
import Typography from "material-ui/Typography";
import * as React from "react";

import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface ProductDetailsCardProps {
  id?: string;
  name?: string;
  description?: string;
  url?: string;
  onBack();
  onDelete();
  onEdit(id: string);
  onShow(url: string);
}

export const ProductDetailsCard: React.StatelessComponent<
  ProductDetailsCardProps
> = ({ onBack, onDelete, onEdit, onShow, id, name, description, url }) => (
  <Card>
    <PageHeader onBack={onBack} title={name}>
      <IconButton onClick={url ? onShow(url) : () => {}} disabled={!url}>
        <VisibilityIcon />
      </IconButton>
      <IconButton onClick={id ? onEdit(id) : () => {}} disabled={!id}>
        <EditIcon />
      </IconButton>
      <IconButton onClick={id ? onEdit(id) : () => {}} disabled={!id}>
        <DeleteIcon />
      </IconButton>
    </PageHeader>
    <CardContent>
      <Typography>
        {description ? (
          description
        ) : description === undefined || description === null ? (
          <Skeleton />
        ) : (
          i18n.t("No description")
        )}
      </Typography>
    </CardContent>
  </Card>
);
export default ProductDetailsCard;
