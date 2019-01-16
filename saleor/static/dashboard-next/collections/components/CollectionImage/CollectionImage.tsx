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
import AddPhotoIcon from "@material-ui/icons/AddAPhoto";
import CardTitle from "../../../components/CardTitle";
import Hr from "../../../components/Hr";
import ImageTile from "../../../components/ImageTile";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { CollectionDetails_collection_backgroundImage } from "../../types/CollectionDetails";

const styles = (theme: Theme) =>
  createStyles({
    PhotosIcon: {
      height: "64px",
      margin: "0 auto",
      width: "64px"
    },
    PhotosIconContainer: {
      margin: `${theme.spacing.unit * 5}px 0`,
      textAlign: "center"
    },
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

export interface CollectionImageProps extends WithStyles<typeof styles> {
  data: {
    backgroundImageAlt: string;
  };
  image: CollectionDetails_collection_backgroundImage;
  onChange: (event: React.ChangeEvent<any>) => void;
  onImageDelete: () => void;
  onImageUpload: (event: React.ChangeEvent<any>) => void;
}

export const CollectionImage = withStyles(styles)(
  class CollectionImageComponent extends React.Component<
    CollectionImageProps,
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
                  color="secondary"
                  onClick={this.clickImgInput}
                >
                  {i18n.t("Upload image")}
                </Button>
                <input
                  className={classes.fileField}
                  id="fileUpload"
                  onChange={onImageUpload}
                  type="file"
                  ref={this.imgInputAnchor}
                />
              </>
            }
          />
          <CardContent>
            {image === undefined ? (
              <div>
                <div className={classes.imageContainer}>
                  <Skeleton />
                </div>
              </div>
            ) : image === null ? (
              <div className={classes.PhotosIconContainer}>
                <AddPhotoIcon className={classes.PhotosIcon} />
              </div>
            ) : (
              <ImageTile image={image} onImageDelete={onImageDelete} />
            )}
          </CardContent>
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
CollectionImage.displayName = "CollectionImage";
export default CollectionImage;
