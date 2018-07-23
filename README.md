# text_cnn_mr
------


## Synopsis
------
1. Use TextCNN model to achieve movie reviews binary classification;
2. Support pretrained word vector as embedding layer (using word2vec);
3. Supoort static and nonstatic embedding layer (by tensorflow parameter definition).
4. Support log train

## Environments
------
1. python3.5.2
2. tensorflow1.4.0

## Data Preprocess
------
1. Run `data_helper.py` to load pretrained word2vec model to build word embedding;
2. Parameter `w2v_flie` can be modified to change word2vec model path. 
3. For me, I use model `GoogleNews-vectors-negative300.bin` here. [Baidu Yun Link](https://pan.baidu.com/s/1xX0U-Z4DGTCol1-BWN133g). Password:`zbiq`.

## Train Model
------
1. Run `train.py` with arguments `--word2vec/rand` and `--static/nonstatic`, and model will be saved at path `/runs/<timestamp>/checkpoints/`.
2. Argument `--word2vec` means using word2vec model as the initial value of embedding layer, `--rand` means initializing embedding layer randomly; 
3. Arguments `--static` means embedding layer will not be updated when training, `--static` means updated.

## Evaluation
------
1. Run `eval.py` to evaluate model. The default config is to evaluate on training data. You can make your own testing data and modify the tf flags `eval_train` to evaluate model on testing data.
2. Argument `--checkpoint_dir` assign model's path, can be modified to use different trained model.
3. I trained 3 models (rand, word2vec-static, word2vec-nonstatic)，each model was trained with 20 epochs. Their accuracy on training data was showed as follows:
| Rand | W2v-static | W2v-nonstatic |
| --- | --- | --- |
|97.477%|96.999%|97.533%|

## References
------
1. [Convolutional Neural Networks for Sentence Classification](https://arxiv.org/abs/1408.5882)
2. [dennybritz/cnn-text-classification-tf](https://github.com/dennybritz/cnn-text-classification-tf/)
3. [JianWenJun/MLDemo](https://github.com/JianWenJun/MLDemo/blob/master/NLP/Text_CNN/text_cnn_main.py)