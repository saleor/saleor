import useRouter from "use-react-router";

export type UseNavigatorResult = (
  url: string,
  replace?: boolean,
  preserveQs?: boolean
) => void;
function useNavigator(): UseNavigatorResult {
  const {
    location: { search },
    history
  } = useRouter();

  return (url: string, replace = false, preserveQs = false) => {
    const targetUrl = preserveQs ? url + search : url;
    replace ? history.replace(targetUrl) : history.push(targetUrl);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
}

export default useNavigator;
