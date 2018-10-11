import { withStyles, WithStyles } from "@material-ui/core/styles";
import * as React from "react";

import Card from "@material-ui/core/Card";
import Button from "@material-ui/core/Button";
import CardContent from "@material-ui/core/CardContent";
import AddPhotoIcon from "@material-ui/icons/AddAPhoto";
import DeleteIcon from "@material-ui/icons/Delete";
import IconButton from "@material-ui/core/IconButton";

import Toggle from "../../../components/Toggle";
import CardTitle from "../../../components/CardTitle";
import ActionDialog from "../../../components/ActionDialog";
import DialogContentText from "@material-ui/core/DialogContentText";

import i18n from "../../../i18n";

interface CategoryBackgroundProps {
  onImageUpload?(event: React.ChangeEvent<any>);
  onImageDelete?: (id: string) => () => void;
  placeholderImage: string;
  backgroundImage?: {
    id?: string;
    url?: string;
  };
}

interface BackgroundImageProps {
  onImageDelete?: (id: string) => () => void;
  backgroundImage?: {
    id?: string;
    url?: string;
  };
}

const decorate = withStyles(theme => ({
  PhotosIcon: {
    height: theme.spacing.unit * 8,
    margin: "0 auto",
    width: theme.spacing.unit * 8
  },
  PhotosIconContainer: {
    margin: `${theme.spacing.unit * 5}px 0`,
    textAlign: "center" as "center"
  },
  fileField: {
    display: "none"
  },
  root: {
    display: "grid" as "grid",
    gridTemplateColumns: "repeat(4, 1fr)"
  },
  image: {
    height: "100%",
    objectFit: "contain" as "contain",
    userSelect: "none" as "none",
    width: "100%"
  },
  imageContainer: {
    "&:hover, &.dragged": {
      "& $imageOverlay": {
        display: "block" as "block"
      }
    },
    justifySelf: "start",
    height: 148,
    width: 148,
    background: "#ffffff",
    border: "1px solid #eaeaea",
    borderRadius: theme.spacing.unit,
    overflow: "hidden" as "hidden",
    padding: theme.spacing.unit * 2,
    position: "relative" as "relative"
  },
  imageOverlay: {
    background: "rgba(0, 0, 0, 0.6)",
    cursor: "pointer",
    display: "none" as "none",
    height: 148,
    left: 0,
    padding: theme.spacing.unit * 2,
    position: "absolute" as "absolute",
    top: 0,
    width: 148
  },
  imageOverlayToolbar: {
    display: "flex" as "flex",
    justifyContent: "flex-end",
    position: "relative" as "relative",
    top: "-10px"
  }
}));

const BackgroundImage = decorate<BackgroundImageProps>(
  ({ classes, onImageDelete, backgroundImage }) => (
    <Toggle>
      {(opened, { toggle }) => (
        <>
          <div className={classes.root}>
            <div className={classes.imageContainer}>
              <div className={classes.imageOverlay}>
                <div className={classes.imageOverlayToolbar}>
                  <IconButton color="secondary" onClick={toggle}>
                    <DeleteIcon />
                  </IconButton>
                </div>
              </div>
              <img className={classes.image} src={backgroundImage.url} />
            </div>
          </div>
          <ActionDialog
            open={opened}
            onClose={toggle}
            onConfirm={() => {
              onImageDelete(backgroundImage.url)();
              toggle();
            }}
            variant="delete"
            title={i18n.t("Remove category image")}
          >
            <DialogContentText>
              {i18n.t("Are you sure you want to delete this image?")}
            </DialogContentText>
          </ActionDialog>
        </>
      )}
    </Toggle>
  )
);

export const CategoryBackground = decorate(
  class CategoryBackgroundClass extends React.Component<
    CategoryBackgroundProps &
      WithStyles<
        | "PhotosIcon"
        | "PhotosIconContainer"
        | "fileField"
        | "root"
        | "image"
        | "imageContainer"
        | "imageOverlay"
        | "imageOverlayToolbar"
      >,
    {}
  > {
    imgInputAnchor = React.createRef<HTMLInputElement>();

    clickImgInput = () => this.imgInputAnchor.current.click();

    render() {
      const {
        classes,
        onImageUpload,
        backgroundImage,
        placeholderImage,
        onImageDelete
      } = this.props;
      return (
        <Card>
          <CardTitle
            title={i18n.t("Background image (optional)")}
            toolbar={
              <>
                <Button
                  variant="flat"
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
            {backgroundImage === undefined ? (
              <div className={classes.root}>
                <div className={classes.imageContainer}>
                  <img className={classes.image} src={placeholderImage} />
                </div>
              </div>
            ) : backgroundImage.url ? (
              <BackgroundImage
                onImageDelete={onImageDelete}
                backgroundImage={backgroundImage}
              />
            ) : (
              <div className={classes.PhotosIconContainer}>
                <AddPhotoIcon className={classes.PhotosIcon} />
              </div>
            )}
          </CardContent>
        </Card>
      );
    }
  }
);

export default CategoryBackground;
