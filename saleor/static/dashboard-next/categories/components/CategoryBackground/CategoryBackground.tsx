import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import CardTitle from "../../../components/CardTitle";
import Hr from "../../../components/Hr";
import ImageTile from "../../../components/ImageTile";
import ImageUpload from "../../../components/ImageUpload";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { CategoryDetails_category_backgroundImage } from "../../types/CategoryDetails";
import { FormData } from "../CategoryUpdatePage";

const styles = (theme: Theme) =>
  createStyles({
    fileField: {
      display: "none"
    },
    image: {
      height: "100%",
      objectFit: "contain",
      userSelect: "none",
      width: "100%"
    },
    imageContainer: {
      background: "#ffffff",
      border: "1px solid #eaeaea",
      borderRadius: theme.spacing.unit,
      height: 148,
      justifySelf: "start",
      overflow: "hidden",
      padding: theme.spacing.unit * 2,
      position: "relative",
      width: 148
    }
  });

export interface CategoryBackgroundProps extends WithStyles<typeof styles> {
  data: FormData;
  image: CategoryDetails_category_backgroundImage;
  onChange: (event: React.ChangeEvent<any>) => void;
  onImageDelete: () => void;
  onImageUpload: (file: File) => void;
}

export const CategoryBackground = withStyles(styles)(
  class CategoryBackgroundComponent extends React.Component<
    CategoryBackgroundProps,
    {}
  > {
    imgInputAnchor = React.createRef<HTMLInputElement>();

    clickImgInput = () => this.imgInputAnchor.current.click();

    render() {
      const {
        classes,
        data,
        onImageUpload,
        image,
        onChange,
        onImageDelete
      } = this.props;
      return (
        <Card>
          <CardTitle
            title={i18n.t("Background image (optional)")}
            toolbar={
              <>
                <Button
                  variant="text"
                  color="primary"
                  onClick={this.clickImgInput}
                >
                  {i18n.t("Upload image")}
                </Button>
                <input
                  className={classes.fileField}
                  id="fileUpload"
                  onChange={event => onImageUpload(event.target.files[0])}
                  type="file"
                  ref={this.imgInputAnchor}
                />
              </>
            }
          />
          {image === undefined ? (
            <CardContent>
              <div>
                <div className={classes.imageContainer}>
                  <Skeleton />
                </div>
              </div>
            </CardContent>
          ) : image === null ? (
            <ImageUpload onImageUpload={onImageUpload} />
          ) : (
            <CardContent>
              <ImageTile image={image} onImageDelete={onImageDelete} />
            </CardContent>
          )}

          {image && (
            <>
              <Hr />
              <CardContent>
                <TextField
                  name="backgroundImageAlt"
                  label={i18n.t("Description")}
                  helperText={i18n.t("Optional")}
                  value={data.backgroundImageAlt}
                  onChange={onChange}
                  fullWidth
                  multiline
                />
              </CardContent>
            </>
          )}
        </Card>
      );
    }
  }
);
CategoryBackground.displayName = "CategoryBackground";
export default CategoryBackground;
