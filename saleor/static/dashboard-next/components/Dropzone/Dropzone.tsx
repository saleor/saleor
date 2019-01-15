import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import { fade } from "@material-ui/core/styles/colorManipulator";
import Typography from "@material-ui/core/Typography";
import AddPhotoIcon from "@material-ui/icons/AddAPhoto";
import classNames from "classnames";
import * as React from "react";
import DropzoneComponent from "react-dropzone";
import i18n from "../../i18n";

interface DropzoneProps {
  onImageUpload: (file: File) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    containerDragActive: {
      background: fade(theme.palette.primary.main, 0.1),
      color: theme.palette.primary.main
    },
    fileField: {
      display: "none"
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
      transition: theme.transitions.duration.standard + "s",
      width: 148
    },
    photosIcon: {
      height: "64px",
      margin: "0 auto",
      width: "64px"
    },
    photosIconContainer: {
      padding: `${theme.spacing.unit * 5}px 0`,
      textAlign: "center"
    },
    uploadText: {
      color: "inherit",
      textTransform: "uppercase"
    }
  });

export const Dropzone = withStyles(styles, { name: "Dropzone" })(
  ({ classes, onImageUpload }: DropzoneProps & WithStyles<typeof styles>) => (
    <DropzoneComponent onDrop={files => onImageUpload(files[0])}>
      {({ isDragActive, getInputProps, getRootProps }) => (
        <div
          {...getRootProps()}
          className={classNames({
            [classes.photosIconContainer]: true,
            [classes.containerDragActive]: isDragActive
          })}
        >
          <input {...getInputProps()} className={classes.fileField} />
          <AddPhotoIcon className={classes.photosIcon} />
          <Typography className={classes.uploadText} variant="body2">
            {i18n.t("Drop here to upload", {
              context: "image upload"
            })}
          </Typography>
        </div>
      )}
    </DropzoneComponent>
  )
);
Dropzone.displayName = "Dropzone";
export default Dropzone;
