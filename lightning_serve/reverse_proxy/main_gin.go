package something

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/jmcvetta/randutil"
)

var routing []map[string][]string

func updateRouting(c *gin.Context) (string, error) {
	bodyAsByteArray, err := ioutil.ReadAll(c.Request.Body)
	if err != nil {
		return "failed", err
	}
	json.Unmarshal([]byte(bodyAsByteArray), &routing)
	return "Updated", nil
}

func handleRouting(c *gin.Context, p string) (interface{}, error) {
	for _, router := range routing {
		choices := make([]randutil.Choice, 0, len(router))
		for prob, urls := range router {
			prob, _ := strconv.Atoi(prob)
			choice := randutil.Choice{
				Weight: int(prob),
				Item:   urls,
			}
			choices = append(choices, choice)
		}
		result, _ := randutil.WeightedChoice(choices)
		var urls, _ = result.Item.([]string)
		for _, url := range urls {
			if c.Request.Method == "GET" {
				resp, err := http.Get(url + p)
				if err != nil {
					return "failed", err
				}
				body, err := ioutil.ReadAll(resp.Body)
				return string(body), err
			} else {
				resp, err := http.Post(url+p, c.GetHeader("Content-Type"), c.Request.Body)
				if err != nil {
					return "failed", err
				}
				body, err := ioutil.ReadAll(resp.Body)
				return string(body), err
			}
		}
	}
	return "Processed", nil
}

func proxyFunc(c *gin.Context) {
	result := make(chan interface{})
	go func(c *gin.Context) {
		proxyPath := c.Param("proxyPath")

		var Body interface{}
		if proxyPath == "/api/v1/proxy" {
			Body, _ = updateRouting(c)
		} else if len(routing) > 0 {
			Body, _ = handleRouting(c, proxyPath)
		}
		result <- Body

	}(c.Copy())
	c.JSON(http.StatusOK, <-result)
}

func main() {
	host := flag.String("host", "0.0.0.0", "Address of the server")
	port := flag.String("port", "8000", "Port of the server")
	flag.Parse()
	r := gin.Default()
	r.Any("/*proxyPath", proxyFunc)
	r.Run(fmt.Sprintf("%s:%s", *host, *port))
}
