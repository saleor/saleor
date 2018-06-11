import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import DeleteIcon from "@material-ui/icons/Delete";
import * as React from "react";

import FileUpload from "../../../components/FileUpload";
import FormSpacer from "../../../components/FormSpacer";
import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface CollectionDetailsProps {
  collection?: {
    id: string;
    name: string;
    backgroundImage: string;
  };
  data?: {
    name: string;
    backgroundImage: string;
  };
  disabled?: boolean;
  onChange?(event: React.ChangeEvent<any>);
  onDelete?();
}

const decorate = withStyles(theme => ({
  image: {
    width: "100%"
  },
  root: {}
}));
const CollectionDetails = decorate<CollectionDetailsProps>(
  ({ classes, collection, data, disabled, onChange, onDelete }) => (
    <Card>
      <PageHeader title={i18n.t("Details")}>
        <IconButton disabled={disabled} onClick={onDelete}>
          <DeleteIcon />
        </IconButton>
      </PageHeader>
      <CardContent>
        <TextField
          fullWidth
          label={i18n.t("Name")}
          name="name"
          onChange={onChange}
          value={data.name}
        />
        <FormSpacer />
        {collection ? (
          <img src={collection.backgroundImage} className={classes.image} />
        ) : (
          <Skeleton />
        )}
        <FormSpacer />
        <FileUpload
          disabled={disabled}
          name="backgroundImage"
          onChange={onChange}
          value={data.backgroundImage}
        />
      </CardContent>
    </Card>
  )
);
CollectionDetails.displayName = "CollectionDetails";
export default CollectionDetails;
