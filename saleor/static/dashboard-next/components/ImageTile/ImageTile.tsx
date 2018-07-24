import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

interface ImageTileProps {}

const decorate = withStyles(theme => ({ root: {} }));
const ImageTile = decorate<ImageTileProps>(({ classes }) => <div />);
ImageTile.displayName = "ImageTile";
export default ImageTile;
