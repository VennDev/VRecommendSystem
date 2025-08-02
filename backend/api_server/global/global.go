package global

import (
	svtype "github.com/venndev/vrecommendation/internal/services/types"
	lgtype "github.com/venndev/vrecommendation/pkg/logger/types"
	kftype "github.com/venndev/vrecommendation/pkg/messaging/types"
	"github.com/venndev/vrecommendation/pkg/setting"
)

var (
	Config       setting.Config
	Logger       lgtype.Logger
	KafkaManager kftype.KafkaManager
	EventService svtype.EventService
)
