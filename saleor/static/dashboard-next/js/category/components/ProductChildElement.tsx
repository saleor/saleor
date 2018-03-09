import * as React from "react";
import Grid from "material-ui/Grid";
import Card, { CardContent, CardMedia } from "material-ui/Card";
import Typography from "material-ui/Typography";
import { Link } from "react-router-dom";
import { withStyles } from "material-ui/styles";
import { grey } from "material-ui/colors";
import { Skeleton } from "../../components/Skeleton";

interface CategoryChildElementProps {
  label: string;
  url: string;
  price: string;
  thumbnail: string;
  loading?: boolean;
}
const decorate = withStyles(theme => ({
  link: {
    textDecoration: "none",
    color: "inherit"
  },
  media: {
    height: 200
  },
  content: {
    height: "5rem"
  },
  price: {
    color: grey[500]
  }
}));
export const ProductChildElement = decorate<CategoryChildElementProps>(
  ({ label, price, url, thumbnail, classes, loading }) => (
    <Grid item xs={6} md={4} lg={3}>
      <Card>
        <Link to={url} className={classes.link}>
          <CardMedia image={thumbnail} className={classes.media} />
          <CardContent className={classes.content}>
            {loading ? (
              <Typography variant={"button"}>
                <Skeleton style={{ width: "80%" }} />
              </Typography>
            ) : (
              <>
                <Typography variant={"button"}>{label}</Typography>
                <Typography className={classes.price}>{price}</Typography>
              </>
            )}
          </CardContent>
        </Link>
      </Card>
    </Grid>
  )
);
