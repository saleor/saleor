import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import Card from "@material-ui/core/Card";
import Button from "@material-ui/core/Button";
import CardContent from "@material-ui/core/CardContent";
import AddPhotoIcon from "@material-ui/icons/AddAPhoto";

import CardTitle from "../../../components/CardTitle";

import i18n from "../../../i18n";

interface CategoryBackgroundProps {
  onImageUpload?(event: React.ChangeEvent<any>);
  disabled: boolean;
}

const decorate = withStyles(theme => ({
  noPhotosIcon: {
    height: theme.spacing.unit * 8,
    margin: "0 auto",
    width: theme.spacing.unit * 8
  },
  noPhotosIconContainer: {
    margin: `${theme.spacing.unit * 5}px 0`,
    textAlign: "center" as "center"
  },
  fileField: {
    display: "none"
  }
}));

export const CategoryBackground = decorate<CategoryBackgroundProps>(
  ({ classes, onImageUpload, disabled }) => {
    return (
      <Card>
        <CardTitle
          title={i18n.t("Background image (optional)")}
          toolbar={
            <>
              <Button
                variant="flat"
                color="secondary"
                disabled={disabled}
                onClick={() => this.upload.click()}
              >
                {i18n.t("Upload image")}
              </Button>
              <input
                className={classes.fileField}
                id="fileUpload"
                onChange={onImageUpload}
                type="file"
                ref={ref => (this.upload = ref)}
              />
            </>
          }
        />
        <CardContent>
          <div className={classes.noPhotosIconContainer}>
            <AddPhotoIcon className={classes.noPhotosIcon} />
          </div>
        </CardContent>
      </Card>
    );
  }
);
export default CategoryBackground;
