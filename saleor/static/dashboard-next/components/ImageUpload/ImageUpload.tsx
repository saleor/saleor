import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import { fade } from "@material-ui/core/styles/colorManipulator";
import Typography from "@material-ui/core/Typography";
import classNames from "classnames";
import * as React from "react";

import i18n from "../../i18n";
import ImageIcon from "../../icons/Image";
import Dropzone from "../Dropzone";

interface ImageUploadProps {
  children?: (props: { isDragActive: boolean }) => React.ReactNode;
  className?: string;
  disableClick?: boolean;
  isActiveClassName?: string;
  iconContainerClassName?: string;
  iconContainerActiveClassName?: string;
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
      color: theme.typography.body1.color,
      textTransform: "uppercase"
    }
  });

export const ImageUpload = withStyles(styles, { name: "ImageUpload" })(
  ({
    children,
    classes,
    className,
    disableClick,
    isActiveClassName,
    iconContainerActiveClassName,
    iconContainerClassName,
    onImageUpload
  }: ImageUploadProps & WithStyles<typeof styles>) => (
    <Dropzone
      disableClick={disableClick}
      onDrop={files => onImageUpload(files[0])}
    >
      {({ isDragActive, getInputProps, getRootProps }) => (
        <>
          <div
            {...getRootProps()}
            className={classNames({
              [classes.photosIconContainer]: true,
              [classes.containerDragActive]: isDragActive,
              [className]: !!className,
              [isActiveClassName]: !!isActiveClassName && isDragActive
            })}
          >
            <div
              className={classNames({
                [iconContainerClassName]: !!iconContainerClassName,
                [iconContainerActiveClassName]:
                  !!iconContainerActiveClassName && isDragActive
              })}
            >
              <input {...getInputProps()} className={classes.fileField} />
              <ImageIcon className={classes.photosIcon} />
              <Typography className={classes.uploadText} variant="body2">
                {i18n.t("Drop here to upload", {
                  context: "image upload"
                })}
              </Typography>
            </div>
          </div>
          {children && children({ isDragActive })}
        </>
      )}
    </Dropzone>
  )
);
ImageUpload.displayName = "ImageUpload";
export default ImageUpload;
