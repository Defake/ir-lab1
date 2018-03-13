(ns crawler.news-extractor
  (:require [clojure.edn :as edn]
            [clojure.java.io :as io]
            [net.cgrand.enlive-html :as html]
            [monger.core :as mg]
            [monger.collection :as mc]
            [clojure.string :as str]))

(def conn (mg/connect))
(def db (mg/get-db conn "ir_lab_texts"))
(def coll "news_texts")

(defn insert-text [source text]
  (mc/insert-and-return db coll {:source source
                                 :text text}))

(defn load-edn
  "Load edn from an io/reader source (filename or io/resource)."
  [source]
  (try
    (with-open [r (io/reader source)]
      (edn/read (java.io.PushbackReader. r)))
    (catch java.io.IOException e
      (printf "Couldn't open '%s': %s\n" source (.getMessage e)))
    (catch RuntimeException e
      (printf "Error parsing edn file '%s': %s\n" source (.getMessage e)))))

(def load (memoize load-edn))

(defn walk-content
  "Returns string-content of all internal nodes"
  [nodes]
  (str/join " "
            (for [node nodes]
              (if (= java.lang.String (class node))
                node
                (walk-content (:content node))))))

(defn extract-tags [from selector]
  (html/select
    (html/html-resource (java.io.StringReader. from))
    selector))

(defn extract-text [tags]
  (-> tags
      (walk-content)
      (str/replace #"[\s\r\n]{2,}" " ")
      (str/trim)))

(defn get-news-texts [path selector tags-preformatter & [amount]]
  (let [pages (load path)]
    (->> (if amount
           (take amount pages)
           pages)
         (map #(extract-tags (:body %) selector))
         (filter not-empty)
         (map #(extract-text (tags-preformatter %))))))

(defn save-texts [source texts]
  (doseq [text texts]
    (insert-text source text)))


;; ===========================================
;;               Extracting news
;; ===========================================

;; ===== Extract rusvesna news =====
;(save-texts "rusvesna"
;  (get-news-texts
;    "/Volumes/MainBrain/Working/Univer/Crawl/texts/rusvesna.clj"
;    [:div.content :article :div.art-postcontent :div.field-name-field-text :p]
;    (fn [tags]
;      (filter
;        (fn [tag]
;          (not-any?
;            #(re-find #"Читайте также" (str (first (:content %))))
;            (:content tag)))
;        tags))))

;; Check
(count (mc/find-maps db coll {:source "rusvesna"}))
;=> 7999

;; ===== Extract ria news =====
;(save-texts "ria"
;  (get-news-texts
;    "/Volumes/MainBrain/Working/Univer/Crawl/ria/corpus/corpus.clj"
;    [:div.b-article__body :> :p]
;    (fn [tags]
;      (clojure.walk/postwalk
;        #(if-not (= :strong (:tag %)) %)
;        tags))))

;; Check
(count (mc/find-maps db coll {:source "ria"}))
;=> 7856


;; ===== Extract rg news =====
;(save-texts "rg"
;  (get-news-texts
;    "/Volumes/MainBrain/Working/Univer/Crawl/Rgru/corpus/corpus"
;    [:div.b-material-wrapper__text :> :p]
;    identity))

;; Check
(count (mc/find-maps db coll {:source "rg"}))
;=> 7335
