(ns crawler.core
  (:require [pegasus.core :as pg]
            [pegasus.dsl :as cr]))

(defn- crawl [start-url news-regex link-selectors save-dir-path]
  (binding [*out* (java.io.StringWriter.)]
    (pg/crawl {:seeds [start-url]
               :user-agent "crawler"
               :extractor (apply cr/defextractors
                                 (for [selector link-selectors]
                                   (cr/extract :at-selector selector
                                               :follow :href
                                               :with-regex news-regex)))
               :corpus-size 8000
               :job-dir save-dir-path})))

(defn crawl-rg-ru []
  (crawl "https://rg.ru/news.html"
         #"rg.ru/\d{4}/\d\d/\d\d/"
         [[:a.b-link_title]
          [:a.b-link]]
         "/Volumes/MainBrain/Working/Univer/Crawl/Rgru"))

(defn crawl-rusvesna []
  (crawl "http://rusvesna.su/news"
         #"rusvesna.su/news/.*"
         [[:div.fr-news-t :a]
          [:div.views-field-field-more-news :ul :li :a]]
         "/Volumes/MainBrain/Working/Univer/Crawl/rusvesna"))

(defn crawl-mk-ru []
  (crawl "http://www.mk.ru"
         #"http://www.mk.ru/\w+/\d{4}/\d\d/\d\d/"
         [[:a.mkh2]
          [:ul.news_list :li :a]
          [:div.left_more :ul :li :a]]
         "/Volumes/MainBrain/Working/Univer/Crawl/mkru"))

(defn crawl-lenta-ru []
  (crawl "https://lenta.ru/"
         #"https://lenta.ru/news/\d{4}/\d\d/\d\d/\S+/"
         [[:section.b-topic-addition :a]
          [:div.item.article :div.titles :a]]
         "/Volumes/MainBrain/Working/Univer/Crawl/lenta"))

(defn crawl-ria-ru []
  (crawl "https://ria.ru/"
         #"https://ria.ru/\S+/\d{8}/\d+.html"
         [[:a.b-index__day-news-item-link]
          [:div.b-index__main-list-place :a]
          [:div.b-inject__article-title :a]
          [:div.b-inject__mega-title :a]]
         "/Volumes/MainBrain/Working/Univer/Crawl/ria"))

;(future (crawl-rg-ru))
;(future (crawl-rusvesna))
;(future (crawl-mk-ru))
;(future (crawl-lenta-ru))
;(future (crawl-ria-ru))