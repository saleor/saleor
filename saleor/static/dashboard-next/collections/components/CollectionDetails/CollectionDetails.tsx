import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import * as classNames from "classnames";
import * as React from "react";

import FileUpload from "../../../components/FileUpload";
import FormSpacer from "../../../components/FormSpacer";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface CollectionDetailsProps {
  collection?: {
    backgroundImage: string;
  };
  data: {
    name: string;
    backgroundImage: string;
  };
  disabled: boolean;
  onChange(event: React.ChangeEvent<any>);
  onImageRemove();
}

const decorate = withStyles(theme => ({
  image: {
    width: "100%"
  },
  link: {
    color: theme.palette.secondary.main,
    cursor: "pointer" as "pointer"
  }
}));
const CollectionDetails = decorate<CollectionDetailsProps>(
  ({ classes, collection, data, disabled, onChange, onImageRemove }) => (
    <Card>
      <CardContent>
        <TextField
          disabled={disabled}
          fullWidth
          label={i18n.t("Name")}
          name="name"
          onChange={onChange}
          value={data.name}
        />
        <FormSpacer />
        {collection ? (
          <>
            <img src={collection.backgroundImage} className={classes.image} />
            <Typography
              variant="caption"
              className={classNames({
                [classes.link]: !disabled
              })}
              onClick={disabled ? undefined : onImageRemove}
            >
              {i18n.t("Remove")}
            </Typography>
          </>
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
