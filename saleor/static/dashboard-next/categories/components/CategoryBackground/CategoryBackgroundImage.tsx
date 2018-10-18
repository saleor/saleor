import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import ImageTile from "../../../components/ImageTile";

const decorate = withStyles({});

interface CategoryBackgroundImageProps {
  onImageDelete: () => void;
  backgroundImage: {
    url: string;
  };
}

const CategoryBackgroundImage = decorate<CategoryBackgroundImageProps>(
  ({ onImageDelete, backgroundImage }) => (
    <ImageTile
      tile={backgroundImage}
      onImageDelete={onImageDelete}
      deleteIcon={true}
      editIcon={false}
    />
  )
);

export default CategoryBackgroundImage;
